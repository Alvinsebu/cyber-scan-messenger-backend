
from flask_jwt_extended import jwt_required, get_jwt

from flask import Blueprint, request, jsonify
from app.models import db, User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields
from webargs.flaskparser import use_args
from flask import current_app

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
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return jsonify(access_token=access_token, refresh_token=refresh_token, email=user.email, username=user.username)
        return jsonify({"msg": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"msg": "Login failed"}), 400


# Endpoint to generate new access token from refresh token
@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)
        return jsonify(access_token=new_access_token)
    except Exception as e:
        return jsonify({"msg": "Token refresh failed"}), 400




# Endpoint to generate new access token from refresh token
@auth.route('/logout', methods=['POST'])
@jwt_required(refresh=True)
def logout():
    try:
        jti = get_jwt()["jti"]
        # Access the blacklist from the app context
        current_app.token_blacklist.add(jti)
        print(current_app.token_blacklist)
        return jsonify({"msg": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"msg": "Logout failed"}), 400

# --- New API: List users with bullying comment count (paginated) ---
from marshmallow import validate
from app.models import Comment

class PaginationSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    limit = fields.Int(load_default=100, validate=validate.Range(min=1, max=1000))

@auth.route('/users/bullying', methods=['GET'])
@jwt_required()
@use_args(PaginationSchema(), location='query')
def list_users_with_bullying(args):
    try:
        page = args['page']
        limit = args['limit']
        users_query = User.query.paginate(page=page, per_page=limit, error_out=False)
        users = users_query.items
        user_ids = [user.id for user in users]
        bullying_counts = dict(
            db.session.query(Comment.user_id, db.func.count(Comment.id))
            .filter(Comment.is_bullying == True, Comment.user_id.in_(user_ids))
            .group_by(Comment.user_id)
            .all()
        )
        result = [
            {
                'username': user.username,
                'bullyinyCommentCount': bullying_counts.get(user.id, 0)
            }
            for user in users
        ]
        response = {
            'users': result,
            'total': users_query.total,
            'pages': users_query.pages,
            'current_page': users_query.page
        }
        return jsonify(response), 200
    except Exception as e:
        print(e)
        return jsonify({'msg': 'Failed to fetch users'}), 400