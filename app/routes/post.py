from flask import Blueprint, request, jsonify
from app.models import db, Post
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields
from webargs.flaskparser import use_args
import boto3

post_bp = Blueprint('post', __name__)

class PostSchema(Schema):
    content = fields.Str(required=True)
    url = fields.Str(required=False) # Add url field


from werkzeug.utils import secure_filename
import os

# S3 configuration
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION')
)
BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@post_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_image():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'msg': 'No file provided'}), 400
            
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'msg': 'No file selected'}), 400
            
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'msg': 'File type not allowed'}), 400

        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Upload file to S3
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': file.content_type
            }
        )

        # Generate URL
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        
        return jsonify({
            'msg': 'File uploaded successfully',
            'url': url
        }), 201

    except Exception as e:
        return jsonify({'msg': 'Failed to upload file'}), 400


@post_bp.route('/post', methods=['POST'])
@jwt_required()
@use_args(PostSchema(), location='json')
def create_post(args):
    try:
        user_id = get_jwt_identity()
        post = Post(
            content=args['content'],
            user_id=user_id,
            url=args.get('url') # Add url to post
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({"msg": "Post created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create post"}), 400
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


@post_bp.route('/post', methods=['GET'])
@jwt_required()
def get_posts():
    try:
        user_id = get_jwt_identity()
        posts = Post.query.filter_by(user_id=user_id).all()
        return jsonify([post.to_dict() for post in posts]), 200
    except Exception as e:
        return jsonify({"msg": "Failed to get posts"}), 400

@post_bp.route('/posts/random', methods=['GET'])
def get_random_posts():
    try:
        # Get page number and size from query params, default to page 1 and 10 items
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Query posts with random order and pagination
        posts = Post.query.order_by(db.func.random())\
                         .paginate(page=page, per_page=per_page, error_out=False)

        # Prepare response data
        response = {
            'posts': [post.to_dict() for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': posts.page
        }
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"msg": "Failed to fetch random posts"}), 400


    