from flask import Flask, jsonify
from app.models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.routes.auth import auth, bcrypt
from app.routes.post import post_bp
from app.routes.comment import comment_bp
from app.routes.health_check import health_check_bp
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
    JWTManager(app)
    CORS(app)

    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(post_bp, url_prefix='/api')
    app.register_blueprint(comment_bp, url_prefix='/api')
    app.register_blueprint(health_check_bp, url_prefix='/')

    # Error handler for validation
    @parser.error_handler
    def handle_error(err, req, schema, *, error_status_code, error_headers):
        res = jsonify({"errors": err.messages})
        res.status_code = error_status_code or 400
        return res

    return app