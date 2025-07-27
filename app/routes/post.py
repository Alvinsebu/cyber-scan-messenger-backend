from flask import Blueprint, request, jsonify
from app.models import db, Post
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields
from webargs.flaskparser import use_args

post_bp = Blueprint('post', __name__)

class PostSchema(Schema):
    content = fields.Str(required=True)

@post_bp.route('/post', methods=['POST'])
@jwt_required()
@use_args(PostSchema(), location='json')
def create_post(args):
    try:
        user_id = get_jwt_identity()
        post = Post(content=args['content'], user_id=user_id)
        db.session.add(post)
        db.session.commit()
        return jsonify({"msg": "Post created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create post"}), 400

    
