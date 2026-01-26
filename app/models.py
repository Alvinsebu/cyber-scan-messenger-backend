from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)

class Post(db.Model):

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    url = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'url': self.url
        }

class Comment(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    is_bullying = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    post_id = db.Column(db.String(36), db.ForeignKey('post.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Message(db.Model):
    """Model for storing chat messages with cyberbullying detection"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    receiver = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    is_bullying = db.Column(db.Boolean, default=False)
    bullying_probability = db.Column(db.Float, default=0.0)
    is_read = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'message': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_bullying': self.is_bullying,
            'bullying_probability': self.bullying_probability,
            'is_read': self.is_read
        }