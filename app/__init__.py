from flask import Flask, jsonify
from app.models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.routes.auth import auth, bcrypt
from app.routes.post import post_bp
from app.routes.comment import comment_bp
from app.routes.health_check import health_check_bp
from app.routes.chat import chat_bp
from app.extensions import socketio
from flask_migrate import Migrate
from app.models import db
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # 🔥 Add this line
from config import Config
from webargs.flaskparser import parser

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    migrate = Migrate(app, db)
    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(post_bp, url_prefix='/api')
    app.register_blueprint(comment_bp, url_prefix='/api')
    app.register_blueprint(health_check_bp, url_prefix='/')
    
    # Register chat blueprint for REST API endpoints
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # Initialize SocketIO with app
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Import socket event handlers after socketio is initialized
    from app.routes import chat  # This registers the socket event handlers

    # JWT Token blacklist set (should be persistent in production)
    token_blacklist = set()

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in token_blacklist

    # Expose blacklist for use in routes
    app.token_blacklist = token_blacklist

    # Error handler for validation
    @parser.error_handler
    def handle_error(err, req, schema, *, error_status_code, error_headers):
        res = jsonify({"errors": err.messages})
        res.status_code = error_status_code or 400
        return res

    return app