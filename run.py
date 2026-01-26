from app import create_app
from app.extensions import socketio

app = create_app()

# Note: Use 'flask db upgrade' to create tables, not db.create_all()
# db.create_all() can cause lock issues in production

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)