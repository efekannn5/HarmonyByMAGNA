from app import create_app
from app.extensions import socketio
from analytics import create_analytics_app
import threading
import time

app = create_app()
analytics_app = create_analytics_app()


def run_analytics_server():
    """Analytics server'ı ayrı thread'de çalıştır (Port 8190)"""
    time.sleep(2)  # Ana sistemin başlaması için kısa bekleme
    print("\n" + "="*70)
    print("ANALYTICS DASHBOARD STARTING - Port 8190")
    print("URL: http://localhost:8190/analytics")
    print("="*70 + "\n")
    analytics_app.run(host="0.0.0.0", port=8190, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Analytics server'ı arka planda başlat
    analytics_thread = threading.Thread(target=run_analytics_server, daemon=True)
    analytics_thread.start()
    
    # Ana sistem başlat (Port 8181)
    host = app.config.get("APP_HOST", "0.0.0.0")
    port = app.config.get("APP_PORT", 8181)
    
    print("\n" + "="*70)
    print("HARMONY ECOSYSTEM - MAIN SYSTEM STARTING - Port 8181")
    print("="*70 + "\n")
    
    # Debug mode kapalı - production environment
    socketio.run(app, host=host, port=port, debug=True, use_reloader=False)
    