workers = 1  # SocketIO için TEK worker (sticky session sorunu önlenir)
worker_class = 'eventlet'  # Required for SocketIO
worker_connections = 1000  # Eventlet için eşzamanlı bağlantı sayısı
bind = '0.0.0.0:8181'
timeout = 300  # Timeout artırıldı (5 dakika)
keepalive = 5  # Keepalive artırıldı - bağlantı kopmalarını önler
max_requests = 1000  # Worker restart sıklığı artırıldı
max_requests_jitter = 100

# Logging
accesslog = '/home/sua_it_ai/controltower/HarmonyEcoSystem/logs/gunicorn_access.log'
errorlog = '/home/sua_it_ai/controltower/HarmonyEcoSystem/logs/gunicorn_error.log'
loglevel = 'info'

# Process naming
proc_name = 'harmonyecosystem'

# Server mechanics
daemon = False
pidfile = '/home/sua_it_ai/controltower/HarmonyEcoSystem/logs/gunicorn.pid'

# -------------------------------------------------------------
# Analytics dashboard (port 8190) launcher inside gunicorn worker
# -------------------------------------------------------------
_analytics_started = False


def _start_analytics():
    """Start analytics Flask app once per worker (runs on 8190)."""
    global _analytics_started
    if _analytics_started:
        return

    from threading import Thread
    from analytics import create_analytics_app

    analytics_app = create_analytics_app()
    host = analytics_app.config.get("ANALYTICS_HOST", "0.0.0.0")
    port = analytics_app.config.get("ANALYTICS_PORT", 8190)

    def _run():
        analytics_app.run(host=host, port=port, debug=False, use_reloader=False)

    Thread(target=_run, daemon=True).start()
    _analytics_started = True


def post_worker_init(worker):
    """Hook: fire analytics server after worker init."""
    _start_analytics()
