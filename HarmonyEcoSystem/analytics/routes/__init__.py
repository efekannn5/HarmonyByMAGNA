"""
Analytics Routes Package
========================
Contains all route handlers for the analytics dashboard.
"""

from .dashboard import analytics_dashboard_bp
from .api import analytics_api_bp

__all__ = ["analytics_dashboard_bp", "analytics_api_bp"]
