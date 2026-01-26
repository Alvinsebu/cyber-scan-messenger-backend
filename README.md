# cyber-scan-messenger-backend

backend service for cyber detection app

# 🛡️ Cyberbullying Detection Web App (Flask + ML)

A full-stack Flask-based API that detects cyberbullying in comments using a trained machine learning model. Users can register, log in, create posts, and comment—while the system flags harmful content.

---

## 🚀 Features

- 🔒 User Authentication (JWT-based)
- 📝 Create Posts and Comments
- 🤖 Cyberbullying Detection using ML
- 🧠 Model trained with TF-IDF + Logistic Regression
- 🔗 MySQL Database
- 🔄 REST API with Flask Blueprints
- 🌐 CORS-enabled for frontend integration

---

## 📦 Tech Stack

- Flask, Flask-JWT-Extended, SQLAlchemy
- scikit-learn, pandas, joblib
- MySQL (via `mysql-connector-python`)
- Marshmallow + Webargs for validation
- CORS and dotenv support

---

## ⚙️ Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/flask_cyberbully_app.git
cd flask_cyberbully_app

### Create Virtual Environment

python -m venv venv
# Activate:
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

### Install Dependencies
pip install -r requirements.txt


## 🔐 Environment Variables
Create a .env file to avoid hardcoding secrets:
SECRET_KEY=****
JWT_SECRET_KEY=****
DATABASE_URL=*****

Update your config.py to read from .env

🧠 Train the ML Model
Use the following to train your model before starting the app:
python train_model.py
It saves the model, tokenizer in models folder.

Ensure you have a CSV named cyberbullying_data.csv with columns: text, lab.

🧪 Initialize Database


python run.py


🧰 API Endpoints

| Endpoint              | Method | Description                  | Auth |
| --------------------- | ------ | ---------------------------- | ---- |
| `/api/register`       | POST   | Register new user            | ❌    |
| `/api/login`          | POST   | Login and get JWT token      | ❌    |
| `/api/post`           | POST   | Create a new post            | ✅    |
| `/api/comment/<post>` | POST   | Add comment & check bullying | ✅    |


📁 Directory Structure

flask_cyberbully_app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── post.py
│   │   └── comment.py
│   └── utils/
│       └── detector.py
├── config.py
├── train_model.py
├── run.py
├── requirements.txt
└── .env (optional, ignored in git)


🛡️ Security Note
Add .env and config.py to .gitignore to avoid pushing secrets:

.env
config.py


📬 Contact
For suggestions or collaboration, contact: [Alvin.Sebastian] – [alvinsebastian779@gmail.com]

---

## 💬 Real-time Chat System with Socket.IO

### 📡 What is Socket.IO?

**Socket.IO** is a library that enables **real-time, bidirectional communication** between clients (browsers/apps) and servers. Unlike traditional HTTP requests where the client must ask for data, Socket.IO maintains an open connection that allows:

- **Instant message delivery** (no polling required)
- **Two-way communication** (server can push data to clients)
- **Event-based messaging** (emit and listen to custom events)
- **Automatic reconnection** and fallback mechanisms

Think of it like a phone call vs. sending letters - Socket.IO keeps the line open for instant back-and-forth conversation.

---

### 🏗️ Architecture Overview

```
┌─────────────┐                    ┌──────────────────┐                    ┌─────────────┐
│   Client A  │◄──── WebSocket ───►│  Flask Server    │◄──── WebSocket ───►│   Client B  │
│  (Browser)  │                    │   + SocketIO     │                    │  (Browser)  │
└─────────────┘                    │   + MySQL DB     │                    └─────────────┘
                                   └──────────────────┘
                                           │
                                           ▼
                                   ┌──────────────────┐
                                   │  ML Model        │
                                   │  (Cyberbullying  │
                                   │   Detection)     │
                                   └──────────────────┘
```

**How it works:**
1. **Client connects** to server via WebSocket (persistent connection)
2. **Server assigns** each user a unique session ID and stores it
3. **Clients send events** (e.g., `send_message`) with data
4. **Server processes** the event, runs ML detection, saves to database
5. **Server emits events** back to specific clients or broadcasts to all

---

### 🔧 Server-Side Implementation

#### Socket.IO Events (Backend)

The server handles these events in [app/routes/chat.py](app/routes/chat.py):

| Event Name       | Triggered By | Purpose                                | Response Event        |
|------------------|--------------|----------------------------------------|-----------------------|
| `connect`        | Client       | New client establishes connection      | `user_joined`, `online_users` |
| `disconnect`     | Client       | Client closes connection               | `online_users`        |
| `send_message`   | Client       | User sends a private message           | `receive_message`, `message_sent` |
| `mark_as_read`   | Client       | User opens/reads messages              | `messages_marked_read` |
| `typing`         | Client       | User is typing in chat input           | `user_typing`         |

#### Connection Flow

```python
@socketio.on('connect')
def handle_connect():
    # 1. Extract username from connection query params
    username = request.args.get('username')
    
    # 2. Store user's socket ID for message routing
    online_users[username] = request.sid
    
    # 3. Create a personal "room" for private messaging
    join_room(username)
    
    # 4. Notify all clients that this user is now online
    emit('user_joined', username, broadcast=True)
    emit('online_users', list(online_users.keys()), broadcast=True)
```

**Key Concepts:**
- **Session ID (`request.sid`)**: Unique identifier for each WebSocket connection
- **Rooms**: Virtual channels - each user joins their own room (username) for private messaging
- **Broadcast**: Sends event to ALL connected clients
- **Room-specific emit**: Sends event only to clients in that room

#### Message Sending with ML Detection

```python
@socketio.on('send_message')
def handle_send_message(data):
    # 1. Extract message data
    sender = data.get('sender')
    receiver = data.get('receiver')
    message_content = data.get('message')
    
    # 2. SECURITY: Verify sender matches connected user
    if online_users.get(sender) != request.sid:
        emit('error', {'message': 'Unauthorized'})
        return
    
    # 3. 🤖 RUN CYBERBULLYING DETECTION
    bullying_result = predict_text(message_content, threshold=0.6)
    is_bullying = bullying_result['label']
    bullying_probability = bullying_result['probability']
    
    # 4. SAVE to database
    new_message = Message(
        sender=sender,
        receiver=receiver,
        content=message_content,
        is_bullying=is_bullying,
        bullying_probability=bullying_probability
    )
    db.session.add(new_message)
    db.session.commit()
    
    # 5. DELIVER to receiver (if online)
    if receiver in online_users:
        emit('receive_message', message_data, room=receiver)
    
    # 6. CONFIRM to sender
    emit('message_sent', {'id': new_message.id, 'status': 'delivered'})
```

---

### 💻 Client-Side Implementation

#### 1️⃣ Installation

Install the Socket.IO client library:

```bash
npm install socket.io-client
```

Or include via CDN:
```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
```

#### 2️⃣ Connect to Server

```javascript
import io from 'socket.io-client';

// Connect with username as query parameter
const socket = io('http://localhost:5000', {
  query: { username: 'alice' },
  transports: ['websocket', 'polling'] // Try WebSocket first, fallback to polling
});

// Check connection status
socket.on('connect', () => {
  console.log('✅ Connected to server! Session ID:', socket.id);
});

socket.on('disconnect', () => {
  console.log('❌ Disconnected from server');
});

socket.on('connect_error', (error) => {
  console.error('Connection failed:', error);
});
```

#### 3️⃣ Send Messages

```javascript
function sendMessage(receiver, messageText) {
  socket.emit('send_message', {
    sender: 'alice',           // Current user's username
    receiver: receiver,        // Recipient's username
    message: messageText,      // Message content
    timestamp: new Date().toISOString()
  });
}

// Example usage
sendMessage('bob', 'Hello Bob! How are you?');
```

#### 4️⃣ Receive Messages

```javascript
// Listen for incoming messages
socket.on('receive_message', (data) => {
  console.log('📩 New message from:', data.sender);
  console.log('Message:', data.message);
  console.log('⚠️ Bullying detected?', data.is_bullying);
  
  // Update UI - add message to chat
  displayMessage(data);
  
  // Show warning if bullying detected
  if (data.is_bullying) {
    showWarning(`This message was flagged as potentially harmful (${(data.bullying_probability * 100).toFixed(0)}% confidence)`);
  }
});

// Confirmation that your message was sent
socket.on('message_sent', (data) => {
  console.log('✅ Message sent! ID:', data.id);
  updateMessageStatus(data.id, data.status); // 'delivered' or 'saved'
  
  if (data.is_bullying) {
    alert('⚠️ Your message contains potentially harmful content and has been flagged.');
  }
});
```

#### 5️⃣ Online Users & Presence

```javascript
// Get list of online users
socket.on('online_users', (users) => {
  console.log('👥 Online users:', users);
  updateOnlineUsersList(users); // Update UI
});

// Someone joined
socket.on('user_joined', (username) => {
  console.log(`${username} is now online`);
  showNotification(`${username} joined the chat`);
});
```

#### 6️⃣ Typing Indicators

```javascript
// Send typing indicator
let typingTimeout;
chatInput.addEventListener('input', () => {
  socket.emit('typing', {
    sender: 'alice',
    receiver: currentChatPartner,
    is_typing: true
  });
  
  // Stop typing after 2 seconds of inactivity
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    socket.emit('typing', {
      sender: 'alice',
      receiver: currentChatPartner,
      is_typing: false
    });
  }, 2000);
});

// Receive typing indicator
socket.on('user_typing', (data) => {
  if (data.is_typing) {
    showTypingIndicator(data.sender);
  } else {
    hideTypingIndicator(data.sender);
  }
});
```

#### 7️⃣ Mark Messages as Read

```javascript
socket.emit('mark_as_read', {
  username: 'alice',
  message_ids: ['msg-id-1', 'msg-id-2', 'msg-id-3']
});

socket.on('messages_marked_read', (data) => {
  console.log(`✓ Marked ${data.count} messages as read`);
});
```

---

### 🔐 Authentication & Security

#### JWT Integration

While Socket.IO handles real-time communication, REST endpoints use JWT for authentication:

```javascript
// 1. Login via REST API to get JWT token
const loginResponse = await fetch('http://localhost:5000/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'alice@example.com', password: 'password123' })
});

const { access_token, username } = await loginResponse.json();

// 2. Connect to Socket.IO with username
const socket = io('http://localhost:5000', {
  query: { username: username }
});

// 3. Use JWT for REST API calls (fetch message history)
const messagesResponse = await fetch('http://localhost:5000/api/chat/messages/bob', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

#### Security Measures

- **Sender verification**: Server checks `request.sid` matches stored session for that username
- **Message persistence**: All messages saved to database (even if recipient offline)
- **Input validation**: Required fields checked before processing
- **Error handling**: Graceful failures with error events emitted to client

---

### 📊 Database Schema

Messages are stored in the `messages` table:

```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    sender VARCHAR(80) NOT NULL,
    receiver VARCHAR(80) NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_bullying BOOLEAN DEFAULT FALSE,
    bullying_probability FLOAT DEFAULT 0.0,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender) REFERENCES user(username),
    FOREIGN KEY (receiver) REFERENCES user(username)
);
```

---

### 🛡️ Cyberbullying Detection Integration

Every message goes through ML analysis:

```python
# In detector.py
def predict_text(text, threshold=0.6):
    # 1. Load trained model (TF-IDF + Neural Network)
    # 2. Preprocess text (tokenization, cleaning)
    # 3. Predict probability of bullying
    # 4. Return result with confidence score
    return {
        'label': is_bullying,
        'probability': confidence_score,
        'found_lexical': harmful_words_detected
    }
```

**Thresholds:**
- **0.6 (60%)**: Message flagged as bullying and marked in database
- **Tracked**: Both comments and messages count toward user's bullying limit
- **Enforcement**: Users exceeding `MAX_BULLYING_COUNT` (default: 5) are blocked from chatting

---

### 🌐 REST API Endpoints (Chat-related)

| Endpoint                          | Method | Auth | Description                                |
|-----------------------------------|--------|------|--------------------------------------------|
| `/api/chat/messages/<username>`   | GET    | ✅    | Get message history with a user            |
| `/api/chat/conversations`         | GET    | ✅    | List all users you've chatted with         |
| `/api/chat/online-users`          | GET    | ✅    | Get all users and their online status      |
| `/api/chat/bullying-report`       | GET    | ✅    | Get your bullying statistics               |
| `/api/chat/can-chat`              | GET    | ✅    | Check if you're allowed to chat (not blocked) |

---

### 🔄 Complete Message Flow Example

```javascript
// ============= ALICE'S CLIENT =============
const aliceSocket = io('http://localhost:5000', {
  query: { username: 'alice' }
});

aliceSocket.on('connect', () => {
  console.log('Alice connected');
  
  // Send message to Bob
  aliceSocket.emit('send_message', {
    sender: 'alice',
    receiver: 'bob',
    message: 'Hey Bob, want to collaborate on the project?',
    timestamp: new Date().toISOString()
  });
});

aliceSocket.on('message_sent', (data) => {
  console.log('✅ Alice: Message sent!', data);
  // data = { id: 'msg-123', status: 'delivered', is_bullying: false }
});

// ============= BOB'S CLIENT =============
const bobSocket = io('http://localhost:5000', {
  query: { username: 'bob' }
});

bobSocket.on('receive_message', (data) => {
  console.log('📩 Bob received:', data.message);
  // data = {
  //   id: 'msg-123',
  //   sender: 'alice',
  //   message: 'Hey Bob, want to collaborate on the project?',
  //   timestamp: '2026-01-26T10:30:00.000Z',
  //   is_bullying: false,
  //   bullying_probability: 0.05
  // }
  
  // Display message in UI
  addMessageToChat(data);
  
  // Mark as read
  bobSocket.emit('mark_as_read', {
    username: 'bob',
    message_ids: [data.id]
  });
});
```

---

### 🚀 Running the Chat Server

```bash
# 1. Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 2. Install dependencies (including Flask-SocketIO)
pip install -r requirements.txt

# 3. Start the server
python run.py

# Server starts on http://localhost:5000
# Socket.IO endpoint: ws://localhost:5000
```

---

### 🧪 Testing with Postman or Browser Console

```javascript
// Open browser console on http://localhost:5000
const socket = io('http://localhost:5000', { query: { username: 'testuser' } });

socket.on('connect', () => console.log('Connected!'));
socket.on('online_users', (users) => console.log('Online:', users));

// Send test message
socket.emit('send_message', {
  sender: 'testuser',
  receiver: 'alice',
  message: 'Hello from browser console!',
  timestamp: new Date().toISOString()
});
```

---

### 📚 Learn More

- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Socket.IO Client API](https://socket.io/docs/v4/client-api/)

---

