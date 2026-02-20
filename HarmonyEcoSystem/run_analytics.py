"""
HarmonyEcoSystem Analytics Server
==================================
Standalone analytics and reporting platform for executives.

This script runs the analytics dashboard on port 8190.
It shares the database with the main application but operates independently.

Usage:
    python3 run_analytics.py

Access:
    http://localhost:8190/analytics
"""

from analytics import create_analytics_app

# Create analytics application
app = create_analytics_app()

if __name__ == "__main__":
    host = app.config.get("ANALYTICS_HOST", "0.0.0.0")
    port = app.config.get("ANALYTICS_PORT", 8190)
    
    app.logger.info("=" * 60)
    app.logger.info("HarmonyEcoSystem Analytics Dashboard")
    app.logger.info("=" * 60)
    app.logger.info(f"Server starting on {host}:{port}")
    app.logger.info(f"Access dashboard at: http://{host}:{port}/analytics")
    app.logger.info("=" * 60)
    
    # Run analytics server (no socketio, no debug for production)
    app.run(
        host=host,
        port=port,
        debug=False,  # Production mode
        use_reloader=False  # Disable auto-reload for stability
    )
