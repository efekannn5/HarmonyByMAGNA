from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta

from flask import Flask

from .extensions import init_extensions, login_manager
from .routes.api import api_bp
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .utils.config_loader import ConfigLoader
from .models import UserAccount


def create_app(config_path: str | None = None) -> Flask:
    config_data = ConfigLoader.load(config_path)

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    _apply_core_config(app, config_data)
    _configure_logging(app, config_data.get("logging", {}))
    _register_template_filters(app, config_data)

    init_extensions(app)
    _register_blueprints(app, config_data)

    app.config["APP_CONFIG"] = config_data

    @login_manager.user_loader
    def load_user(user_id: str):
        return UserAccount.query.get(int(user_id))

    # Database monitoring başlat
    _setup_database_monitoring(app)

    return app


def _apply_core_config(app: Flask, config: Dict[str, Any]) -> None:
    app_config = config.get("app", {})
    db_config = config.get("database", {})

    app.config["SECRET_KEY"] = app_config.get("secret_key", "unsafe-secret")
    app.config["ENV"] = app_config.get("environment", "development")
    app.config["APP_HOST"] = app_config.get("host", "127.0.0.1")
    app.config["APP_PORT"] = int(app_config.get("port", 5000))

    app.config["SQLALCHEMY_DATABASE_URI"] = _build_database_uri(db_config)
    app.config["SQLALCHEMY_ECHO"] = bool(db_config.get("echo", False))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # SQLAlchemy connection pool ayarları - performans optimizasyonu
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,  # Bağlantı havuzu boyutu
        "pool_recycle": 3600,  # 1 saat sonra bağlantıları yenile
        "pool_pre_ping": True,  # Bağlantıyı kullanmadan önce test et
        "pool_timeout": 30,  # Bağlantı bekleme süresi
        "max_overflow": 20,  # Pool doluyken ek bağlantı sayısı
        "echo_pool": False
    }


def _configure_logging(app: Flask, logging_cfg: Dict[str, Any]) -> None:
    level = getattr(logging, logging_cfg.get("level", "INFO"))
    app.logger.setLevel(level)

    log_file = logging_cfg.get("file")
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_path,
            maxBytes=int(logging_cfg.get("rotation", 10_485_760)),
            backupCount=5,
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        handler.setLevel(level)
        app.logger.addHandler(handler)
        
        # LOG_FILE_PATH'i app config'e ekle (admin logs sayfası için)
        app.config["LOG_FILE_PATH"] = log_file


def _register_blueprints(app: Flask, config_data: Dict[str, Any]) -> None:
    api_prefix = config_data.get("app", {}).get("api_prefix", "/api")
    app.register_blueprint(api_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)


def _build_database_uri(db_config: Dict[str, Any]) -> str:
    dialect = db_config.get("dialect", "sqlite")
    if dialect.startswith("sqlite"):
        db_path = db_config.get("database", "instance/app.db")
        return f"sqlite:///{db_path}"

    username = db_config.get("username", "")
    password = db_config.get("password", "")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 1433)
    database = db_config.get("database", "")
    params = []
    driver = db_config.get("driver")
    if driver:
        params.append(("driver", driver))
    options = db_config.get("options", {})
    if isinstance(options, dict):
        params.extend(options.items())

    query = ""
    if params:
        encoded = "&".join(f"{key}={str(value).replace(' ', '+')}" for key, value in params)
        query = f"?{encoded}"

    return f"{dialect}://{username}:{password}@{host}:{port}/{database}{query}"


def _setup_database_monitoring(app: Flask) -> None:
    """Database monitoring servisini kur ve başlat"""
    try:
        from .services.database_monitor import db_monitor
        
        # App referansını ver ve monitoring'i başlat
        db_monitor.start_monitoring(app)
        
        # Graceful shutdown için atexit handler
        import atexit
        def shutdown_monitoring():
            if db_monitor.is_running:
                db_monitor.stop_monitoring()
                app.logger.info("🛑 Database monitoring shutdown")
        
        atexit.register(shutdown_monitoring)
        
    except Exception as e:
        app.logger.error(f"Failed to setup database monitoring: {e}")


def _register_template_filters(app: Flask, config: Dict[str, Any]) -> None:
    tz = _resolve_app_timezone(config)

    @app.template_filter("local_dt")
    def local_dt(value: Optional[datetime], fmt: str = "%d.%m.%Y %H:%M") -> str:
        if not value:
            return "-"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(tz).strftime(fmt)


def _resolve_app_timezone(config: Dict[str, Any]):
    tz_name = config.get("app", {}).get("timezone", "Europe/Istanbul")
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(tz_name)
    except Exception:
        if tz_name in {"Europe/Istanbul", "UTC+3", "TRT", "Turkey"}:
            return timezone(timedelta(hours=3))
        return timezone.utc
