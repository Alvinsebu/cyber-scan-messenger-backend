from flask import Blueprint, request, jsonify
from app.models import db, User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from marshmallow import Schema, fields
from webargs.flaskparser import use_args

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

class RegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email = fields.Str(required=True)

class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)

@auth.route('/register', methods=['POST'])
@use_args(RegisterSchema(), location='json')
def register(args):
    try:
        hashed = bcrypt.generate_password_hash(args['password']).decode('utf-8')
        user = User(username=args['username'], password=hashed, email = args['email'])
        db.session.add(user)
        db.session.commit()
        return jsonify({"msg": "Registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Registration failed"}), 400


@auth.route('/login', methods=['POST'])
@use_args(LoginSchema(), location='json')
def login(args):
    try:
        user = User.query.filter_by(email=args['email']).first()
        if user and bcrypt.check_password_hash(user.password, args['password']):
            token = create_access_token(identity=user.id)
            return jsonify(access_token=token)
        return jsonify({"msg": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"msg": "Login failed"}), 400