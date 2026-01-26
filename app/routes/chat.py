"""
Real-time chat routes with Socket.IO and cyberbullying detection
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio
from app.models import db, Message, User, Comment
from app.utils.detector import predict_text
from datetime import datetime
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)

# Store online users: {username: socket_id}
online_users = {}


# ============================================
# Socket.IO Event Handlers
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    username = request.args.get('username')
    
    if not username:
        print("Connection rejected: No username provided")
        return False
    
    # Store user's socket ID
    online_users[username] = request.sid
    
    # Join a personal room for private messaging
    join_room(username)
    
    print(f'✅ {username} connected with session ID: {request.sid}')
    
    # Notify all clients about the new user
    emit('user_joined', username, broadcast=True)
    
    # Send updated online users list to all clients
    emit('online_users', list(online_users.keys()), broadcast=True)
    
    return True


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    # Find username by session ID
    username = None
    for user, sid in list(online_users.items()):
        if sid == request.sid:
            username = user
            break
    
    if username:
        # Remove from online users
        del online_users[username]
        
        # Leave personal room
        leave_room(username)
        
        # Update online users list for all clients
        emit('online_users', list(online_users.keys()), broadcast=True)
        
        print(f'❌ {username} disconnected')


@socketio.on('send_message')
def handle_send_message(data):
    """
    Handle private message sending with cyberbullying detection
    
    Expected data format:
    {
        "sender": "username",
        "receiver": "username",
        "message": "text content",
        "timestamp": "ISO format timestamp"
    }
    """
    try:
        sender = data.get('sender')
        receiver = data.get('receiver')
        message_content = data.get('message')
        timestamp_str = data.get('timestamp')
        
        # Validate input
        if not all([sender, receiver, message_content]):
            emit('error', {'message': 'Missing required fields'})
            return
        
        # Security check: verify sender matches connected user
        if online_users.get(sender) != request.sid:
            emit('error', {'message': 'Unauthorized: Sender mismatch'})
            print(f"⚠️ Unauthorized message attempt from {sender}")
            return
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.utcnow()
        
        # 🔍 CYBERBULLYING DETECTION
        bullying_result = predict_text(message_content, threshold=0.6)
        is_bullying = bool(bullying_result['label'])
        bullying_probability = bullying_result['probability']
        
        print(f"📝 Message from {sender} to {receiver}")
        if is_bullying:
            print(f"⚠️ BULLYING DETECTED! Probability: {bullying_probability:.2f}")
            print(f"   Found words: {bullying_result.get('found_lexical', [])}")
        
        # Save message to database
        new_message = Message(
            sender=sender,
            receiver=receiver,
            content=message_content,
            timestamp=timestamp,
            is_bullying=is_bullying,
            bullying_probability=bullying_probability,
            is_read=False
        )
        db.session.add(new_message)
        db.session.commit()
        
        # Prepare message data for transmission
        message_data = {
            'id': new_message.id,
            'sender': sender,
            'message': message_content,
            'timestamp': timestamp.isoformat(),
            'is_bullying': is_bullying,
            'bullying_probability': bullying_probability
        }
        
        # Send to receiver if online (to their personal room)
        if receiver in online_users:
            emit('receive_message', message_data, room=receiver)
            print(f"✉️ Message delivered to {receiver}")
        else:
            print(f"📭 {receiver} is offline - message saved to database")
        
        # Confirm to sender
        emit('message_sent', {
            'id': new_message.id,
            'status': 'delivered' if receiver in online_users else 'saved',
            'is_bullying': is_bullying
        })
        
    except Exception as e:
        print(f"❌ Error handling message: {str(e)}")
        emit('error', {'message': f'Failed to send message: {str(e)}'})
        db.session.rollback()


@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    """Mark messages as read"""
    try:
        message_ids = data.get('message_ids', [])
        username = data.get('username')
        
        # Verify user authorization
        if online_users.get(username) != request.sid:
            return
        
        # Update messages
        Message.query.filter(
            Message.id.in_(message_ids),
            Message.receiver == username
        ).update({'is_read': True}, synchronize_session=False)
        
        db.session.commit()
        
        emit('messages_marked_read', {'count': len(message_ids)})
        
    except Exception as e:
        print(f"❌ Error marking messages as read: {str(e)}")
        db.session.rollback()


@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    sender = data.get('sender')
    receiver = data.get('receiver')
    is_typing = data.get('is_typing', False)
    
    # Send typing status to receiver if online
    if receiver in online_users:
        emit('user_typing', {
            'sender': sender,
            'is_typing': is_typing
        }, room=receiver)


# ============================================
# REST API Endpoints
# ============================================

@chat_bp.route('/messages/<username>', methods=['GET'])
@jwt_required()
def get_messages(username):
    """
    Get message history between current user and specified user
    Query params:
    - limit: number of messages to return (default: 50)
    - offset: pagination offset (default: 0)
    """
    current_user_id = get_jwt_identity()
    
    # Get current user's username from ID
    current_user_obj = User.query.get(current_user_id)
    if not current_user_obj:
        return jsonify({'msg': 'User not found'}), 404
    
    current_username = current_user_obj.username
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    print(f"Fetching messages between {current_username} and {username} (limit={limit}, offset={offset})")
    
    # Fetch messages between the two users
    messages = Message.query.filter(
        or_(
            and_(Message.sender == current_username, Message.receiver == username),
            and_(Message.sender == username, Message.receiver == current_username)
        )
    ).order_by(Message.timestamp.desc()).limit(limit).offset(offset).all()
    
    # Mark received messages as read
    unread_message_ids = [
        msg.id for msg in messages 
        if msg.receiver == current_username and not msg.is_read
    ]
    
    if unread_message_ids:
        Message.query.filter(Message.id.in_(unread_message_ids)).update(
            {'is_read': True}, 
            synchronize_session=False
        )
        db.session.commit()
    
    # Return messages in chronological order (oldest first)
    return jsonify({
        'messages': [msg.to_dict() for msg in reversed(messages)],
        'total': len(messages),
        'has_more': len(messages) == limit
    }), 200


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get list of users the current user has chatted with"""
    current_user_id = get_jwt_identity()
    
    # Get current user's username from ID
    current_user_obj = User.query.get(current_user_id)
    if not current_user_obj:
        return jsonify({'msg': 'User not found'}), 404
    
    current_username = current_user_obj.username
    
    # Get unique users from sent and received messages
    sent_to = db.session.query(Message.receiver).filter(
        Message.sender == current_username
    ).distinct().all()
    
    received_from = db.session.query(Message.sender).filter(
        Message.receiver == current_username
    ).distinct().all()
    
    # Combine and deduplicate
    conversation_users = set([user[0] for user in sent_to] + [user[0] for user in received_from])
    
    # Get unread count for each conversation
    conversations = []
    for username in conversation_users:
        unread_count = Message.query.filter(
            Message.sender == username,
            Message.receiver == current_username,
            Message.is_read == False
        ).count()
        
        # Get last message
        last_message = Message.query.filter(
            or_(
                and_(Message.sender == current_username, Message.receiver == username),
                and_(Message.sender == username, Message.receiver == current_username)
            )
        ).order_by(Message.timestamp.desc()).first()
        
        conversations.append({
            'username': username,
            'unread_count': unread_count,
            'last_message': last_message.to_dict() if last_message else None,
            'is_online': username in online_users
        })
    
    # Sort by last message timestamp
    conversations.sort(
        key=lambda x: x['last_message']['timestamp'] if x['last_message'] else '',
        reverse=True
    )
    
    return jsonify({'conversations': conversations}), 200


@chat_bp.route('/online-users', methods=['GET'])
@jwt_required()
def get_online_users():
    """Get list of currently online users"""
    current_user_id = get_jwt_identity()
    
    # Get current user's username from ID
    current_user_obj = User.query.get(current_user_id)
    if not current_user_obj:
        return jsonify({'msg': 'User not found'}), 404
    
    current_username = current_user_obj.username
    
    # Get all users except current user
    users = User.query.filter(User.username != current_username).all()
    
    users_list = [{
        'username': user.username,
        'email': user.email,
        'is_online': user.username in online_users
    } for user in users]
    
    return jsonify({'users': users_list}), 200


@chat_bp.route('/bullying-report', methods=['GET'])
@jwt_required()
def get_bullying_report():
    """Get statistics about bullying messages (for monitoring/admin)"""
    current_user_id = get_jwt_identity()
    
    # Get current user's username from ID
    current_user_obj = User.query.get(current_user_id)
    if not current_user_obj:
        return jsonify({'msg': 'User not found'}), 404
    
    current_username = current_user_obj.username
    
    # Messages sent to current user that were flagged as bullying
    received_bullying = Message.query.filter(
        Message.receiver == current_username,
        Message.is_bullying == True
    ).count()
    
    # Messages sent by current user that were flagged as bullying
    sent_bullying = Message.query.filter(
        Message.sender == current_username,
        Message.is_bullying == True
    ).count()
    
    return jsonify({
        'received_bullying_count': received_bullying,
        'sent_bullying_count': sent_bullying,
        'warning': 'Bullying behavior is monitored and may result in account restrictions'
    }), 200


@chat_bp.route('/can-chat', methods=['GET'])
@jwt_required()
def can_chat():
    """
    Check if current user is allowed to chat based on bullying count
    Returns whether user can chat by comparing total bullying instances
    (comments + messages) against MAX_BULLYING_COUNT
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get current user's username from ID
        current_user_obj = User.query.get(current_user_id)
        if not current_user_obj:
            return jsonify({'msg': 'User not found'}), 404
        
        current_username = current_user_obj.username
        
        # Get MAX_BULLYING_COUNT from config
        max_bullying_count = current_app.config.get('MAX_BULLYING_COUNT', 5)
        
        # Count bullying comments by this user
        bullying_comments_count = Comment.query.filter(
            Comment.user_id == current_user_id,
            Comment.is_bullying == True
        ).count()
        
        # Count bullying chat messages sent by this user
        bullying_messages_count = Message.query.filter(
            Message.sender == current_username,
            Message.is_bullying == True
        ).count()
        
        # Total bullying count
        total_bullying_count = bullying_comments_count + bullying_messages_count
        
        # Check if user can chat
        can_chat = total_bullying_count < max_bullying_count
        
        return jsonify({
            'can_chat': can_chat,
            'is_blocked': not can_chat,
            'bullying_count': total_bullying_count,
            'max_allowed': max_bullying_count,
            'breakdown': {
                'bullying_comments': bullying_comments_count,
                'bullying_messages': bullying_messages_count
            },
            'warning': 'Excessive bullying behavior may result in chat restrictions' if not can_chat else None
        }), 200
        
    except Exception as e:
        print(f"❌ Error checking chat eligibility: {str(e)}")
        return jsonify({'msg': 'Failed to check chat eligibility'}), 500

