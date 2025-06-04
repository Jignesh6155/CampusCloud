from flask import render_template, request, jsonify
from app import app
from datetime import datetime

# In-memory chat storage with channels for each unit
chats = {
    "ENG101": {
        "general": [],
        "assignments": [],
        "resources": []
    },
    "CSC202": {
        "general": [],
        "assignments": [],
        "resources": []
    },
    "MKT305": {
        "general": [],
        "assignments": [],
        "resources": []
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/post-forum')
def post_forum():
    return render_template('post_forum.html')

@app.route('/units-chat')
def units_chat():
    return render_template('units_chat.html')

@app.route('/units/<unit_code>')
def unit_chat(unit_code):
    return render_template('chat_ui.html', unit_code=unit_code)

@app.route('/units/<unit_code>/messages', methods=['GET', 'POST'])
def unit_messages(unit_code):
    # Get the requested channel from the query params
    channel = request.args.get('channel', 'general')

    # Ensure the unit and channel exist
    if unit_code not in chats:
        # Initialize unit with empty channels if not present
        chats[unit_code] = {
            "general": [],
            "assignments": [],
            "resources": []
        }
    if channel not in chats[unit_code]:
        # Initialize the requested channel if not present
        chats[unit_code][channel] = []

    if request.method == 'POST':
        new_msg = request.form.get('message')
        if new_msg:
            # Create a message object with a timestamp
            msg_obj = {
                "message": new_msg,
                "author": "Anonymous User",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            # Append the new message to the correct channel
            chats[unit_code][channel].append(msg_obj)
            return jsonify({"status": "success"})

    # GET request: return the list of messages for the requested channel
    return jsonify(chats[unit_code][channel])
