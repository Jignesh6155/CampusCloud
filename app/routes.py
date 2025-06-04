from flask import render_template, request, jsonify
from app import app
from datetime import datetime

# In-memory chat storage for units
chats = {
    "ENG101": {"general": [], "assignments": [], "resources": []},
    "CSC202": {"general": [], "assignments": [], "resources": []},
    "MKT305": {"general": [], "assignments": [], "resources": []}
}

# In-memory chat storage for committees
committee_chats = {
    "TechCommittee": {"main": [], "general": []},
    "MarketingCommittee": {"main": [], "general": []}
}

# In-memory meetup storage for study groups/social groups
meetups = []

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
        chats[unit_code] = {"general": [], "assignments": [], "resources": []}
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

@app.route('/committee-chat')
def committee_chat():
    return render_template('committee_chat_landing.html')

@app.route('/committee/<committee_name>')
def committee_ui(committee_name):
    is_authorized = False  # Example toggle for testing
    return render_template('committee_ui.html', committee_name=committee_name, is_authorized=is_authorized)

@app.route('/committee/<committee_name>/messages', methods=['GET', 'POST'])
def committee_messages(committee_name):
    channel = request.args.get('channel', 'general')

    if committee_name not in committee_chats:
        committee_chats[committee_name] = {"announcements": [], "general": []}

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

# --------------------
# Study Groups / Meetups
# --------------------
@app.route('/study-groups')
def study_groups():
    return render_template('study_group.html', meetups=meetups)

@app.route('/study-groups/create', methods=['POST'])
def create_meetup():
    topic = request.form.get('topic')
    location = request.form.get('location')
    datetime_str = request.form.get('datetime')
    mtype = request.form.get('type')
    description = request.form.get('description')
    tags = request.form.get('tags', '').split(',')

    if topic and location and datetime_str and mtype:
        meetup = {
            "id": len(meetups) + 1,
            "topic": topic,
            "location": location,
            "datetime": datetime_str,
            "type": mtype,
            "description": description,
            "tags": [tag.strip() for tag in tags if tag.strip()],
            "rsvp_count": 0
        }
        meetups.append(meetup)
        return jsonify({"status": "success", "meetup": meetup})
    return jsonify({"status": "error", "message": "Missing required fields"})

@app.route('/study-groups/rsvp/<int:meetup_id>', methods=['POST'])
def rsvp_meetup(meetup_id):
    for meetup in meetups:
        if meetup["id"] == meetup_id:
            meetup["rsvp_count"] += 1
            return jsonify({"status": "success", "rsvp_count": meetup["rsvp_count"]})
    return jsonify({"status": "error", "message": "Meetup not found"})

# --------------------
# Profile Page
# --------------------
@app.route('/profile')
def profile_landing_page():
    user_data = {
        "name": "John Doe",
        "job_title": "Software Engineer at TechCorp",
        "bio": "Passionate about technology and building great products. Coffee lover ☕️.",
        "hobbies": ["Photography", "Traveling", "Coding challenges"],
        "email": "johndoe@email.com",
        "phone": "+1 (123) 456-7890",
        "profile_picture": "/static/profile-picture.jpg",
        "cover_picture": "/static/profile-cover.jpg",
        "posts": [
            {
                "author": "John Doe",
                "timestamp": "2 hours ago",
                "text": "Excited to start a new coding project today! 🚀"
            },
            {
                "author": "John Doe",
                "timestamp": "Yesterday at 6:00 PM",
                "text": "Throwback to my trip to the mountains last summer. 🏞️",
                "image": "/static/mountains.jpg"
            }
        ]
    }
    return render_template('profile_landingpage.html', user=user_data)

# --------------------
# Group Assignments Page
# --------------------
@app.route('/group-assignments')
def group_assignments():
    # Future: Fetch user's groups and members from the database
    return render_template('group_assignment.html')

@app.route('/group-assignments/<group_name>')
def group_assignment_chat(group_name):
    # Future: Fetch messages, files, members, etc. for the group
    return render_template('group_assignment_chatui.html', group_name=group_name)