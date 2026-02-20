"""
HarmonyEcoSystem Analytics Module
==================================
Management Dashboard and Analytics Platform

This module provides read-only analytics and reporting for executives.
It runs on a separate port (8190) and does not interfere with operational system (8181).

Features:
- Real-time KPI monitoring
- Performance analytics by line, operator, shift
- Bottleneck detection and alerts
- Historical trend analysis
- Executive reporting

Architecture:
- Shared database with main app (read-only views)
- Shared services from main app (DollyService, etc.)
- Independent Flask app with separate port
- Dedicated templates and static files
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from flask import Flask
from flask_login import LoginManager

from app.extensions import db, init_extensions
from app.utils.config_loader import ConfigLoader
from .routes.dashboard import analytics_dashboard_bp
from .routes.api import analytics_api_bp


# Initialize Flask-Login for analytics
analytics_login_manager = LoginManager()


def create_analytics_app(config_path: str | None = None) -> Flask:
    """
    Create and configure the analytics Flask application.
    
    Args:
        config_path: Optional path to config file (defaults to main config.yaml)
    
    Returns:
        Configured Flask application instance
    """
    # Load configuration (use main app config)
    config_data = ConfigLoader.load(config_path)
    
    # Create Flask app with separate template/static folders
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
        static_url_path="/analytics/static"
    )
    
    # Apply configuration
    _apply_analytics_config(app, config_data)
    _configure_logging(app, config_data.get("logging", {}))
    
    # Initialize extensions (database only, no socketio for analytics)
    init_extensions(app)
    
    # Initialize Flask-Login
    analytics_login_manager.init_app(app)
    analytics_login_manager.login_view = "analytics_dashboard.login"
    analytics_login_manager.login_message = "Please login to access analytics dashboard"
    
    @analytics_login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import UserAccount
        return UserAccount.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(analytics_dashboard_bp)
    app.register_blueprint(analytics_api_bp, url_prefix="/analytics/api")
    
    # Store config for access in views
    app.config["APP_CONFIG"] = config_data
    
    app.logger.info("Analytics application initialized successfully")
    app.logger.info(f"Analytics dashboard will run on port {app.config.get('ANALYTICS_PORT', 8190)}")
    
    return app


def _apply_analytics_config(app: Flask, config: Dict[str, Any]) -> None:
    """Apply configuration specific to analytics app."""
    app_config = config.get("app", {})
    db_config = config.get("database", {})
    
    # Basic Flask config
    app.config["SECRET_KEY"] = app_config.get("secret_key", "unsafe-secret")
    app.config["ENV"] = app_config.get("environment", "development")
    
    # Analytics-specific config
    app.config["ANALYTICS_PORT"] = 8190
    app.config["ANALYTICS_HOST"] = "0.0.0.0"
    
    # Database config (same as main app - READ ONLY via views)
    from app import _build_database_uri
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_database_uri(db_config)
    app.config["SQLALCHEMY_ECHO"] = False  # Disable SQL logging for analytics
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Optimized connection pool for analytics (read-heavy workload)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,  # Smaller pool for read-only
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "max_overflow": 10,
        "echo_pool": False
    }


def _configure_logging(app: Flask, logging_cfg: Dict[str, Any]) -> None:
    """Configure logging for analytics app."""
    level = getattr(logging, logging_cfg.get("level", "INFO"))
    app.logger.setLevel(level)
    
    # Separate log file for analytics
    log_file = logging_cfg.get("file", "logs/app.log")
    analytics_log_file = log_file.replace("app.log", "analytics.log")
    
    log_path = Path(analytics_log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = RotatingFileHandler(
        log_path,
        maxBytes=int(logging_cfg.get("rotation", 10_485_760)),
        backupCount=5,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [ANALYTICS] %(name)s %(message)s")
    )
    handler.setLevel(level)
    app.logger.addHandler(handler)
