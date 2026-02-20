from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    # This is used for development with SocketIO
    host = app.config.get("APP_HOST", "0.0.0.0")
    port = app.config.get("APP_PORT", 8181)
    socketio.run(app, host=host, port=port, debug=True)
