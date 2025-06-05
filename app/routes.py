from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user, login_user  # Added login_user here!
from app.models import User
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('routes', __name__)

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

@bp.route('/signup', methods=['POST'])
def signup():
    full_name = request.form.get('full_name')  # FIXED: match HTML form!
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password or not full_name:
        flash('All fields are required.')
        return redirect(url_for('routes.index'))

    if User.query.filter_by(email=email).first():
        flash('Email already registered!')
        return redirect(url_for('routes.index'))

    user = User(full_name=full_name, email=email)  # Save full_name!
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('Account created! Please login.')
    return redirect(url_for('routes.index'))

@bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    print("Login attempt:", email, password)

    user = User.query.filter_by(email=email).first()
    print("User fetched:", user)

    if user and user.check_password(password):
        print("Password is correct!")
        login_user(user)  # Use Flask-Login's login_user!
        flash('Login successful!')
        return redirect(url_for('routes.profile_landing_page'))
    else:
        print("Invalid email or password.")

    flash('Invalid email or password')
    return redirect(url_for('routes.index'))

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/base')
def base():
    return render_template('base.html')

@bp.route('/post-forum')
def post_forum():
    return render_template('post_forum.html')

@bp.route('/units-chat')
def units_chat():
    return render_template('units_chat.html')

@bp.route('/units/<unit_code>')
def unit_chat(unit_code):
    return render_template('chat_ui.html', unit_code=unit_code)

@bp.route('/units/<unit_code>/messages', methods=['GET', 'POST'])
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

@bp.route('/committee-chat')
def committee_chat():
    return render_template('committee_chat_landing.html')

@bp.route('/committee/<committee_name>')
def committee_ui(committee_name):
    is_authorized = False  # Example toggle for testing
    return render_template('committee_ui.html', committee_name=committee_name, is_authorized=is_authorized)

@bp.route('/committee/<committee_name>/messages', methods=['GET', 'POST'])
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
@bp.route('/study-groups')
def study_groups():
    return render_template('study_group.html', meetups=meetups)

@bp.route('/study-groups/create', methods=['POST'])
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

@bp.route('/study-groups/rsvp/<int:meetup_id>', methods=['POST'])
def rsvp_meetup(meetup_id):
    for meetup in meetups:
        if meetup["id"] == meetup_id:
            meetup["rsvp_count"] += 1
            return jsonify({"status": "success", "rsvp_count": meetup["rsvp_count"]})
    return jsonify({"status": "error", "message": "Meetup not found"})

# --------------------
# Profile Page
# --------------------
@bp.route('/profile')
@login_required
def profile_landing_page():
    # Example user data – in real use, you’d pull this from current_user
    user_data = {
        "name": current_user.full_name,
        "job_title": "Software Engineer at TechCorp",  # Example field
        "bio": "Passionate about technology and building great products. Coffee lover ☕️.",
        "hobbies": ["Photography", "Traveling", "Coding challenges"],
        "email": current_user.email,
        "phone": "+1 (123) 456-7890",
        "profile_picture": "/static/profile-picture.jpg",
        "cover_picture": "/static/profile-cover.jpg",
        "posts": [
            {
                "author": current_user.full_name,
                "timestamp": "2 hours ago",
                "text": "Excited to start a new coding project today! 🚀"
            },
            {
                "author": current_user.full_name,
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
@bp.route('/group-assignments')
def group_assignments():
    return render_template('group_assignment.html')

@bp.route('/group-assignments/<group_name>')
def group_assignment_chat(group_name):
    return render_template('group_assignment_chatui.html', group_name=group_name)

@bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    # Grab form data
    full_name = request.form.get('full_name')
    job_title = request.form.get('job_title')
    bio = request.form.get('bio')
    hobbies = request.form.get('hobbies', '').split(',')
    profile_picture = request.files.get('profile_picture')
    cover_picture = request.files.get('cover_picture')

    # Update the current_user object
    current_user.full_name = full_name
    current_user.job_title = job_title
    current_user.bio = bio
    current_user.hobbies = [h.strip() for h in hobbies if h.strip()]

    # Example: Just log filenames now; real file handling can be added
    if profile_picture:
        print("New profile picture:", profile_picture.filename)
    if cover_picture:
        print("New cover picture:", cover_picture.filename)

    # Save updates
    db.session.commit()
    flash('Profile updated successfully!')

    return redirect(url_for('routes.profile_landing_page'))

@bp.route('/edit-profile', methods=['GET'])
@login_required
def edit_profile():
    # This simply renders the editprofile.html template
    return render_template('editprofile.html', user=current_user)
