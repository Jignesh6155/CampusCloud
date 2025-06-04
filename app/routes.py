from flask import render_template, request, jsonify
from app import app
from datetime import datetime

# In-memory chat storage for units
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

# In-memory chat storage for committees
committee_chats = {
    "TechCommittee": {
        "main": [],
        "general": []
    },
    "MarketingCommittee": {
        "main": [],
        "general": []
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
    channel = request.args.get('channel', 'general')

    if unit_code not in chats:
        chats[unit_code] = {
            "general": [],
            "assignments": [],
            "resources": []
        }
    if channel not in chats[unit_code]:
        chats[unit_code][channel] = []

    if request.method == 'POST':
        new_msg = request.form.get('message')
        if new_msg:
            msg_obj = {
                "message": new_msg,
                "author": "Anonymous User",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            chats[unit_code][channel].append(msg_obj)
            return jsonify({"status": "success"})

    return jsonify(chats[unit_code][channel])

# Committee chat landing page
@app.route('/committee-chat')
def committee_chat():
    return render_template('committee_chat_landing.html')

# Committee chat UI
@app.route('/committee/<committee_name>')
def committee_ui(committee_name):
    is_authorized = False  # Example toggle for testing
    return render_template('committee_ui.html', committee_name=committee_name, is_authorized=is_authorized)

@app.route('/committee/<committee_name>/messages', methods=['GET', 'POST'])
def committee_messages(committee_name):
    channel = request.args.get('channel', 'general')

    if committee_name not in committee_chats:
        committee_chats[committee_name] = {
            "announcements": [],
            "general": []
        }

    if channel not in committee_chats[committee_name]:
        committee_chats[committee_name][channel] = []

    if request.method == 'POST':
        new_msg = request.form.get('message')
        if new_msg:
            msg_obj = {
                "message": new_msg,
                "author": "Anonymous User",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            committee_chats[committee_name][channel].append(msg_obj)
            return jsonify({"status": "success"})

    return jsonify(committee_chats[committee_name][channel])
