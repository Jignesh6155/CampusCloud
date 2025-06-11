from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user, login_user, logout_user
from app.forms import LoginForm, SignupForm  # Import your WTForms
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from app import db
from app.models import Post, Comment, User, Committee, CommentVote  # ✅ Added CommentVote here


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
    form = SignupForm()
    if form.validate_on_submit():
        student_number = form.student_number.data.strip()
        email = form.email.data.strip()
        password = form.password.data
        display_name = form.full_name.data.strip() or student_number  # Use student_number as fallback

        # Check for existing user by email
        if User.query.filter_by(email=email).first():
            flash('Student email already registered!', 'danger')
            return redirect(url_for('routes.index'))

        # Create user (NOTE: using display_name, not full_name)
        user = User(
            display_name=display_name,
            email=email,
            student_number=student_number
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('routes.index'))

    flash('Please fix the errors in the form.', 'danger')
    return redirect(url_for('routes.index'))

@bp.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    print('Form errors:', form.errors)  # Debugging

    if form.validate_on_submit():
        student_number = form.student_number.data.strip()
        password = form.password.data

        user = User.query.filter_by(student_number=student_number).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')

            # ✅ Check if "next" param is safe
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('routes.profile_landing_page')
            return redirect(next_page)

        else:
            flash('Invalid student number or password.', 'danger')
            return redirect(url_for('routes.index'))

    flash('Please fix the errors in the form.', 'danger')
    return redirect(url_for('routes.index'))


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https') and
        ref_url.netloc == test_url.netloc
    )

@bp.route('/')
def index():
    login_form = LoginForm()
    signup_form = SignupForm()
    return render_template('index.html', login_form=login_form, signup_form=signup_form)


@bp.route('/base')
def base():
    return render_template('base.html')


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
from app.models import Post  # make sure to import Post at the top

@bp.route('/profile')
@login_required
def profile_landing_page():
    return render_template('profile_landingpage.html', user=current_user, Post=Post)


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
    # Basic fields
    display_name = request.form.get('display_name')  # <-- updated field name!
    job_title = request.form.get('job_title')
    bio = request.form.get('bio')
    profile_picture = request.files.get('profile_picture')
    cover_picture = request.files.get('cover_picture')

    # New fields
    university = request.form.get('university')
    faculty = request.form.get('faculty')
    major = request.form.get('major')
    student_number = request.form.get('student_number')
    phone = request.form.get('phone')
    quote = request.form.get('quote')  # Use correct form field name
    skills_raw = request.form.get('skills', '')

    # Update user profile fields
    current_user.display_name = display_name  # <-- updated field assignment!
    current_user.job_title = job_title
    current_user.bio = bio
    current_user.university = university
    current_user.faculty = faculty
    current_user.major = major
    current_user.student_number = student_number
    current_user.phone = phone
    current_user.quote = quote

    # Process skills
    skills_list = [skill.strip() for skill in skills_raw.split(',') if skill.strip()]
    current_user.skills_list = skills_list

    # Upload new profile picture if provided
    if profile_picture and profile_picture.filename != '':
        filename = secure_filename(profile_picture.filename)
        profile_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        profile_picture.save(profile_path)
        current_user.profile_picture = f'/static/uploads/{filename}'

    # Upload new cover picture if provided
    if cover_picture and cover_picture.filename != '':
        filename = secure_filename(cover_picture.filename)
        cover_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        cover_picture.save(cover_path)
        current_user.cover_picture = f'/static/uploads/{filename}'

    # Save to the database
    db.session.commit()
    flash('Profile updated successfully!')
    return redirect(url_for('routes.profile_landing_page'))




@bp.route('/edit-profile', methods=['GET'])
@login_required
def edit_profile():
    # This simply renders the editprofile.html template
    return render_template('editprofile.html', user=current_user)


@bp.route('/create-post', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    image_file = request.files.get('image')

    if not content:
        flash('Content is required.', 'error')
        return redirect(url_for('routes.post_forum'))

    image_url = None
    if image_file and image_file.filename != '':
        # Save the uploaded image to static/uploads
        filename = secure_filename(image_file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)  # Ensure folder exists
        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)
        image_url = f'static/uploads/{filename}'

    post = Post(
        title=title,
        content=content,
        author=current_user,
        image_url=image_url
    )
    db.session.add(post)
    db.session.commit()

    flash('Post created!', 'success')
    return redirect(url_for('routes.post_forum'))
    
@bp.route('/post/<int:post_id>')
def post_thread(post_id):
    post = Post.query.get_or_404(post_id)

    # Sort top-level comments by score, descending
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).all()
    comments.sort(key=lambda c: (c.score, c.created_at), reverse=True)

    return render_template('post_threadUI.html', post=post, comments=comments)

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    comment = Comment(content=content, post_id=post_id, user_id=current_user.id)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'author_name': current_user.display_name,  # FIXED: use display_name instead of full_name
        'timestamp': comment.created_at.strftime('%b %d, %Y %I:%M %p'),
        'content': comment.content
    })

@bp.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def add_reply(comment_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    parent_comment = Comment.query.get_or_404(comment_id)
    reply = Comment(
        content=content,
        post_id=parent_comment.post_id,
        user_id=current_user.id,
        parent_id=comment_id
    )
    db.session.add(reply)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'author_name': current_user.display_name,  # FIXED: use display_name
        'timestamp': reply.created_at.strftime('%b %d, %Y %I:%M %p'),
        'content': reply.content
    })
@bp.route('/comment/<int:comment_id>/delete', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id and comment.post.author.id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Delete all associated votes first
    for vote in comment.votes:
        db.session.delete(vote)

    # Load replies explicitly
    db.session.refresh(comment, ['replies'])

    # Now delete the comment (replies will be deleted via cascade)
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'status': 'success'})

@bp.route('/post-forum')
@login_required
def post_forum():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('post_forum.html', posts=posts)

@bp.route('/delete-post/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author.id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/like-post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    if current_user in post.likers:
        # Unlike the post
        post.likers.remove(current_user)
        liked = False
    else:
        # Like the post
        post.likers.append(current_user)
        liked = True

    db.session.commit()

    # Get the updated number of likes
    like_count = post.likers.count()

    return jsonify({
        'likes': like_count,
        'liked': liked
    })

@bp.route('/search-users', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query', '').strip()
    if not query:
        flash('Please enter a search query.', 'warning')
        return redirect(url_for('routes.profile_landing_page'))

    # Search users by display name or email (case-insensitive)
    search_pattern = f"%{query}%"
    results = User.query.filter(
        (User.display_name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
    ).all()

    return render_template('search_results.html', query=query, results=results)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('routes.index'))

@bp.route('/api/search-users')
@login_required
def api_search_users():
    query = request.args.get('query', '').strip()
    users = []
    if query:
        users = User.query \
            .filter(User.display_name.ilike(f'%{query}%')) \
            .limit(10).all()  # limit for performance

    results = [
        {
            'id': u.id,
            'display_name': u.display_name or '(No Name)',
            'profile_picture': u.profile_picture or 'https://cdn-icons-png.flaticon.com/512/149/149071.png',
            'university': u.university or ''  # <-- ADD THIS LINE
        } for u in users
    ]
    return jsonify(results)

@bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile_landingpage.html', user=user, Post=Post)

@bp.route('/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    data = request.get_json()
    vote_value = data.get('vote')  # Expected to be +1 or -1

    if vote_value not in [1, -1]:
        return jsonify({'error': 'Invalid vote value'}), 400

    comment = Comment.query.get_or_404(comment_id)

    # Check if the user has already voted on this comment
    existing_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if existing_vote:
        if existing_vote.vote == vote_value:
            # User clicked the same vote again -> remove vote (toggle off)
            db.session.delete(existing_vote)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'new_score': comment.score,
                'user_vote': 0  # No active vote anymore
            })
        else:
            # Change vote
            existing_vote.vote = vote_value
            db.session.commit()
    else:
        # Add a new vote
        new_vote = CommentVote(user_id=current_user.id, comment_id=comment_id, vote=vote_value)
        db.session.add(new_vote)
        db.session.commit()

    # After update, get the final user vote
    final_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    return jsonify({
        'status': 'success',
        'new_score': comment.score,
        'user_vote': final_vote.vote if final_vote else 0
    })
    
@bp.route('/toggle-follow/<int:user_id>', methods=['POST'])
@login_required
def toggle_follow(user_id):
    user_to_follow = User.query.get_or_404(user_id)

    if user_to_follow == current_user:
        return jsonify({'error': 'You cannot follow yourself.'}), 400

    if current_user in user_to_follow.followers:
        # Unfollow
        user_to_follow.followers.remove(current_user)
        followed = False
    else:
        # Follow
        user_to_follow.followers.append(current_user)
        followed = True

    db.session.commit()

    return jsonify({
        'status': 'success',
        'followed': followed,
        'followers_count': user_to_follow.followers_count,
        'campus_followers_count': user_to_follow.campus_followers_count
    })