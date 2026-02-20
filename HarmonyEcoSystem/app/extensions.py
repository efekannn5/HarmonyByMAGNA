from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# SocketIO optimizasyonu: ping timeout ve interval artırıldı, bağlantı kopması önlendi
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode='eventlet',
    ping_timeout=60,      # 60 saniye timeout (varsayılan 5)
    ping_interval=25,     # 25 saniyede bir ping (varsayılan 25)
    engineio_logger=False,  # Gereksiz logları kapat
    logger=False
)
cache = Cache()


def init_extensions(app):
    """Bind extensions to the current Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    socketio.init_app(app)
    
    # Cache yapılandırması - bellek optimizasyonu
    app.config['CACHE_TYPE'] = 'SimpleCache'  # Basit bellek cache
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 dakika varsayılan timeout
    app.config['CACHE_THRESHOLD'] = 500  # Maksimum 500 cache item
    cache.init_app(app)
