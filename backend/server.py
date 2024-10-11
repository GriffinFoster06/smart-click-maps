# backend/server.py

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import asyncio
from chatclicks import ChatClicks
import eventlet
import os
import jwt
import requests
import threading

# Monkey-patch for compatibility with eventlet
eventlet.monkey_patch()

# Configuration Variables
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_SECRET = os.environ.get('TWITCH_SECRET')
TWITCH_JWT_PUBLIC_KEY_URL = 'https://id.twitch.tv/oauth2/keys'
CHANNEL_ID = os.environ.get('CHANNEL_ID')  # Your Twitch Channel ID
SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')

# Ensure required environment variables are set
if not TWITCH_CLIENT_ID or not TWITCH_SECRET or not CHANNEL_ID:
    raise Exception("Missing environment variables. Ensure TWITCH_CLIENT_ID, TWITCH_SECRET, and CHANNEL_ID are set.")

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Fetch Twitch Public Keys for JWT Validation
def get_twitch_public_keys():
    response = requests.get(TWITCH_JWT_PUBLIC_KEY_URL)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch Twitch public keys.")

TWITCH_PUBLIC_KEYS = get_twitch_public_keys()

def validate_jwt(token):
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']
        key = next((k for k in TWITCH_PUBLIC_KEYS['keys'] if k['kid'] == kid), None)
        if key is None:
            return None
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(token, public_key, algorithms=['RS256'], audience=TWITCH_CLIENT_ID)
        return payload  # Return the payload for further use
    except Exception as e:
        print(f"JWT Validation Error: {e}")
        return None

# Initialize ChatClicks
cc = ChatClicks(
    channel_id=CHANNEL_ID,
    sub_only=False,
    allow_anonymous=False,
    max_poll_time=10,
    sub_boost=1,
    priority_boost=19,
    priority_votes=20,
    tug_weight=5,
    dimensions="1920x1080",
    ban_list=[],
    check_coords_func=None,  # Define if needed
    poll_callback=None       # To be defined below
)

# Define the poll callback to emit data to frontend
async def poll_handler(center, poll_dict):
    if center is None:
        return
    # Emit the processed click data to all connected frontend clients
    socketio.emit('click_data', center)

# Assign the poll_callback
cc.poll_callback = poll_handler

# Start ChatClicks in a background task
def start_chatclicks():
    cc.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(cc.loop)
    cc.loop.run_until_complete(cc.start())

threading.Thread(target=start_chatclicks).start()

# API endpoint for testing
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "Backend server is running."})

# Handle incoming user clicks from frontend
@socketio.on('user_click')
def handle_user_click(data):
    token = data.get('token', '')
    payload = validate_jwt(token)
    if not payload:
        print("Invalid token. Click ignored.")
        emit('error', {'message': 'Invalid authentication token.'})
        return

    # Extract user information from the token payload
    opaque_id = payload.get('opaque_user_id')
    user_id = payload.get('user_id')  # Will be None if the user is not logged in
    is_subscriber = payload.get('role') == 'subscriber'

    # Normalize coordinates
    x_norm = data.get('x')
    y_norm = data.get('y')
    action = data.get('action', 'leftClick')

    if x_norm is None or y_norm is None:
        emit('error', {'message': 'Invalid click data.'})
        return

    # Prepare data for ChatClicks
    click_data = {
        "opaque_id": opaque_id or 'anonymous',
        "login_name": user_id or 'anonymous',
        "x": x_norm,
        "y": y_norm,
        "subscribed": is_subscriber,
        "action": action
    }

    # Add click data to ChatClicks
    asyncio.run_coroutine_threadsafe(
        cc.add_data(click_data, action.replace('Click', '').lower()),
        cc.loop
    )

    # Optionally, emit acknowledgment
    emit('ack', {'message': 'Click received.'})

# Serve frontend files if needed (optional)
@app.route('/frontend/<path:path>')
def serve_frontend(path):
    return send_from_directory('frontend/public', path)

# Run Flask with SocketIO
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
