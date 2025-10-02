from flask import Blueprint, request, jsonify
from app.models import db, Comment
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.detector import is_bullying
from marshmallow import Schema, fields
from webargs.flaskparser import use_args

comment_bp = Blueprint('comment', __name__)

class CommentSchema(Schema):
    content = fields.Str(required=True)

@comment_bp.route('/comment/<string:post_id>', methods=['POST'])
@jwt_required()
@use_args(CommentSchema(), location='json')
def comment(args, post_id):
    try:
        user_id = get_jwt_identity()
        is_bully = is_bullying(args['content'])
        comment = Comment(content=args['content'], user_id=user_id, post_id=post_id, is_bullying=is_bully)
        db.session.add(comment)
        db.session.commit()
        return jsonify({"msg": "Comment added", "isCyberbullying": is_bully})
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create comment"}), 400
    
@comment_bp.route('/comments/<string:post_id>', methods=['GET'])
def get_comments(post_id):
    try:
        comments = Comment.query.filter_by(post_id=post_id).all()
        comments_list = [{
            'id': comment.id,
            'content': comment.content,
            'user_id': comment.user_id,
            'is_bullying': comment.is_bullying,
            'created_at': comment.created_at
        } for comment in comments]
        return jsonify(comments_list)
    except Exception as e:
        return jsonify({"msg": "Failed to fetch comments"}), 400