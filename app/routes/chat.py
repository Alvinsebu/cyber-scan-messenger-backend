from flask import Blueprint, request
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio

chat_bp = Blueprint('chat', __name__)

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    username = data.get('username')
    join_room(room)
    emit('status', {'msg': f'{username} has entered the room.'}, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    username = data.get('username')
    leave_room(room)
    emit('status', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    username = data.get('username')
    msg = data.get('msg')
    emit('message', {'username': username, 'msg': msg}, room=room)
