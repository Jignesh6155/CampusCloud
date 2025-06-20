import os
from datetime import datetime
import pandas as pd

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, session, current_app, abort
)
from flask_login import (
    login_required, current_user, login_user, logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app import db, socketio
from app.models import User, Forum, Post, Comment, Committee, CommentVote, UnitMessage
from app.forms import LoginForm, SignupForm
from app.utils.domain import UNIVERSITY_EMAIL_DOMAINS, sanitize_domain, UNIVERSITY_SLUG_TO_NAME

from flask_socketio import join_room, emit  # ✅ Needed for real-time chat

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
        email = form.email.data.strip().lower()
        password = form.password.data
        display_name = form.full_name.data.strip() or student_number

        # ✅ Sanitize university domain
        cleaned_uni = sanitize_domain(email)

        # ✅ Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('routes.index'))

        # ✅ Create forum if it doesn't exist
        existing_forum = Forum.query.filter_by(university_domain=cleaned_uni).first()
        if not existing_forum:
            new_forum = Forum(name=cleaned_uni.capitalize(), university_domain=cleaned_uni)
            db.session.add(new_forum)
            db.session.commit()  # 🔥 Commit forum immediately so test can find it

        # ✅ Create new user
        user = User(
            display_name=display_name,
            email=email,
            student_number=student_number,
            university=cleaned_uni
        )
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Unexpected error during signup. Please try again.', 'danger')
            return redirect(url_for('routes.index'))

        return redirect(url_for('routes.index'))

    flash('Please fix the errors in the form.', 'danger')
    if form.errors:
        print('Signup form errors:', form.errors)

    return redirect(url_for('routes.index'))

@bp.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    print('Form errors:', form.errors)
    print('Form data:', request.form)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        print('email:', email)
        print('password:', password)

        user = User.query.filter_by(email=email).first()
        print('User found:', user)

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')

            # Determine the next page
            next_page = request.args.get('next')
            if not next_page or not url_parse(next_page).netloc == '':
                next_page = url_for('routes.profile_landing_page')

            # Instead of redirecting immediately, render a transition screen
            return render_template('login_success.html', redirect_url=next_page)

        else:
            flash('Invalid email or password.', 'danger')
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

@bp.route('/forums')
@login_required
def landing_forums():
    # --- 1️⃣  Find Cross-University forum (slug/domain contains "cross") ---
    cross_uni = Forum.query.filter(
        Forum.university_domain.ilike("%cross%")
    ).first()

    # --- 2️⃣  Use sanitizer to get user's university name ------------------
    user_email = current_user.email.lower()
    uni_name = sanitize_domain(user_email)  # e.g. "University of Western Australia"

    user_forum = None
    if uni_name and (not cross_uni or uni_name.lower() != cross_uni.name.lower()):
        user_forum = Forum.query.filter(
            Forum.name.ilike(f"%{uni_name}%")
        ).first()

    # --- 3️⃣  Exclude pinned forums (cross & user) from main list ----------
    pinned_ids = {f.id for f in [cross_uni, user_forum] if f}

    other_forums = Forum.query.filter(~Forum.id.in_(pinned_ids)).order_by(Forum.name.asc()).all()

    return render_template(
        "landingforum.html",
        cross_uni=cross_uni,
        user_forum=user_forum,
        forums=other_forums,
    )


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

@bp.route('/create-post', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    image_file = request.files.get('image')

    if not content:
        flash('Content is required.', 'error')
        return redirect(request.referrer or url_for('routes.general_forum'))

    image_url = None
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)
        image_url = f'static/uploads/{filename}'

    # ✅ Match user's university domain to a forum
    domain = current_user.university.lower()
    forum = Forum.query.filter(Forum.university_domain.ilike(f"%{domain}%")).first()

    # ❗ Safely assign forum_id (None = general forum)
    forum_id = forum.id if forum else None

    post = Post(
        title=title,
        content=content,
        author=current_user,
        image_url=image_url,
        forum_id=forum_id
    )

    db.session.add(post)
    db.session.commit()

    flash('Post created!', 'success')

    # ✅ Redirect to forum if matched, else to general
    if forum:
        return redirect(url_for('routes.forum', slug=forum.university_domain.split('.')[0].lower()))
    return redirect(url_for('routes.general_forum'))

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



    
@bp.route('/post/<int:post_id>')
def post_thread(post_id):
    post = Post.query.get_or_404(post_id)

    # Sort top-level comments by score, descending
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).all()
    comments.sort(key=lambda c: (c.score, c.created_at), reverse=True)

    # Determine where the post came from
    if post.forum_id is None:
        back_url = url_for('routes.general_forum')  # or 'routes.post_forum' if that's your preferred route
        back_label = "Cross-Uni Forum"
    else:
        slug = post.forum.university_domain.split('.')[0].lower()
        back_url = url_for('routes.forum', slug=slug)
        back_label = f"{post.forum.name} Forum"

    return render_template(
        'post_threadUI.html',
        post=post,
        comments=comments,
        back_url=back_url,
        back_label=back_label
    )

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
    posts = Post.query.filter(Post.forum_id == None).order_by(Post.created_at.desc()).all()
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


@bp.route('/forum/<slug>')
@login_required
def forum(slug):
    slug_lower = slug.lower().strip()

    # 🔹 First, try to load an actual Forum row (covers cross-uni, UWA, Curtin, …)
    forum = Forum.query.filter(
        Forum.university_domain.ilike(f"%{slug_lower}%")
    ).first()

    if forum:
        posts = (Post.query
                 .options(joinedload(Post.author))
                 .filter(Post.forum_id == forum.id)
                 .order_by(Post.created_at.desc())
                 .all())
        return render_template(
            "university_forum.html",
            university=forum.name,
            posts=posts,
            forum_slug=slug_lower          # e.g. "cross-uni"
        )

    # 🔹 Legacy GENERAL feed (posts with no forum_id)
    if slug_lower == "general":
        posts = (Post.query
                 .options(joinedload(Post.author))
                 .filter(Post.forum_id.is_(None))
                 .order_by(Post.created_at.desc())
                 .all())
        return render_template(
            "university_forum.html",
            university="Cross-University",
            posts=posts,
            forum_slug="general"
        )

    flash(f"No forum found for “{slug}”.", "warning")
    return redirect(url_for("routes.landing_forums"))



# 🔷 Route 2 — Manually created static forums (avoid collision by using `/forums/`)
@bp.route('/forums/<name>')
def view_forum(name):
    forum = Forum.query.filter(Forum.name.ilike(f"%{name}%")).first()

    if not forum:
        flash("Forum doesn't exist. Redirected to general forum.", "warning")
        return redirect(url_for('routes.general_forum'))

    posts = forum.posts.order_by(Post.created_at.desc()).all()

    return render_template('forum.html', forum=forum, posts=posts)





@bp.route('/general-forum')
@login_required
def general_forum():
    not_found = request.args.get('not_found')  # optional slug if redirected
    posts = Post.query.options(joinedload(Post.author))\
        .filter(Post.forum_id == None)\
        .order_by(Post.created_at.desc())\
        .all()

    return render_template(
        'university_forum.html',
        university="GENERAL",        # always shows "Cross-University Forum"
        posts=posts
    )

@bp.route('/create-post/<slug>', methods=['POST'])
@login_required
def create_post_forum(slug):
    """
    Create a post inside any forum.

    • Regular DB forums:  'uwa', 'curtin', 'cross-uni', …
    • Legacy “general”   :  no Forum row → forum_id = None
    """
    slug = slug.lower().strip()

    # 1️⃣  Find the matching Forum row (if any)
    forum = Forum.query.filter(
        Forum.university_domain.ilike(f"%{slug}%")
    ).first()

    # Legacy: treat “general” as the null-forum feed
    if slug == "general":
        forum = None            # ➜ forum_id = None

    if not forum and slug != "general":
        flash("Forum not found.", "warning")
        return redirect(url_for("routes.landing_forums"))

    # 2️⃣  Form fields
    title   = request.form.get("title", "").strip() or None
    content = request.form.get("content", "").strip()
    if not content:
        flash("Content is required.", "error")
        return redirect(request.referrer or url_for("routes.landing_forums"))

    # 3️⃣  Optional image
    image_url = None
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        upload_path = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_path, exist_ok=True)
        image_file.save(os.path.join(upload_path, filename))
        image_url = f"static/uploads/{filename}"

    # 4️⃣  Save post
    post = Post(
        title=title,
        content=content,
        user_id=current_user.id,
        forum_id=forum.id if forum else None,
        image_url=image_url
    )
    db.session.add(post)
    db.session.commit()
    flash("Post created!", "success")

    # 5️⃣  Redirect back to the same forum
    return redirect(url_for("routes.forum", slug=slug))


@bp.route('/units-chat')
@login_required
def units_chat():
    university = sanitize_domain(current_user.email)

    if university == "University of Western Australia":
        df = pd.read_excel("app/data/Units_UWA.xlsx")
        df.columns = df.columns.str.strip()  # Clean column names
        units = df.to_dict(orient="records")
    else:
        units = []

    return render_template("units_chat.html", units=units, university=university)

# 🔹 Load chat UI for a specific unit
@bp.route('/units/<unit_code>')
@login_required
def unit_chat(unit_code):
    return render_template(
        'chat_ui.html',
        unit_code=unit_code,
        current_user=current_user
    )

# 🔹 GET / POST messages
# 🔹 GET / POST messages
@bp.route("/units/<unit_code>/messages", methods=["GET", "POST"])
@login_required
def unit_messages(unit_code):
    channel = request.args.get("channel", "general")

    # ---------- POST ----------
    if request.method == "POST":
        data      = request.get_json() or request.form
        new_msg   = (data.get("message") or "").strip()
        parent_id = data.get("parent_id")          # may be None / ""

        if not new_msg:
            return jsonify({"status": "empty"}), 400

        msg = UnitMessage(
            unit_code = unit_code.upper(),
            channel   = channel,
            message   = new_msg,
            author    = current_user.display_name or "Anonymous User",
            user_id   = current_user.id,
            parent_id = parent_id or None          # store if provided
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({"status": "success", "id": msg.id})

    # ---------- GET ----------
    messages = (
        db.session.query(UnitMessage, User)
        .join(User, UnitMessage.user_id == User.id)
        .filter(UnitMessage.unit_code == unit_code.upper(),
                UnitMessage.channel   == channel)
        .order_by(UnitMessage.timestamp.asc())
        .all()
    )

    result = [{
        "id"             : m.id,
        "message"        : m.message,
        "author"         : u.display_name or "Anonymous",
        "user_id"        : m.user_id,
        "profile_picture": u.profile_picture or "/static/default-avatar.png",
        "timestamp"      : m.timestamp.isoformat(),
        "parent_id"      : m.parent_id            # 🔸 include!
    } for m, u in messages]

    return jsonify(result)


# 🔹 DELETE message (RESTful path + short alias) -----------------
@bp.route('/units/<unit_code>/messages/<int:msg_id>', methods=['DELETE'])
@bp.route('/delete-message/<int:msg_id>', methods=['DELETE'])   # matches JS fetch
@login_required
def delete_unit_message(unit_code=None, msg_id=None):
    """Delete one message if the current user owns it."""
    msg = UnitMessage.query.get_or_404(msg_id)

    # If the long RESTful route is used, verify unit_code matches
    if unit_code and msg.unit_code != unit_code:
        return jsonify({"error": "Message does not belong to this unit"}), 400

    if msg.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    room = f"{msg.unit_code}_{msg.channel}"
    db.session.delete(msg)
    db.session.commit()

    # Optional: notify everyone else in the room
    socketio.emit('message_deleted', {"id": msg_id}, to=room)

    return jsonify({"success": True})

# ---------- Socket.IO handlers ----------------
@socketio.on('join')
def handle_join(data):
    room = f"{data['unit_code']}_{data['channel']}"
    join_room(room)
    print(f"🟢 {data.get('author', 'Unknown')} joined {room}")

@socketio.on("send_message")
def handle_send_message(data):
    room = f"{data['unit_code']}_{data['channel']}"
    join_room(room)

    try:
        message = UnitMessage(
            unit_code = data["unit_code"],
            channel   = data["channel"],
            message   = data["message"],
            user_id   = int(data["user_id"]),
            author    = data["author"],
            parent_id = data.get("parent_id"),      # 🔸 NEW
            timestamp = datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        print("✅ Message committed:", message)
    except Exception as e:
        print("❌ DB save error:", e)
        return

    emit("receive_message", {
        "id"        : message.id,
        "unit_code" : message.unit_code,
        "channel"   : message.channel,
        "message"   : message.message,
        "author"    : message.author,
        "user_id"   : message.user_id,
        "timestamp" : message.timestamp.isoformat(),
        "parent_id" : message.parent_id           # 🔸 include!
    }, to=room)
    
@bp.route("/units/<unit_code>/assignments")
@login_required
def unit_assignments_channel(unit_code):
    # Only top-level posts (parent_id is NULL) so replies are injected by JS
    assignment_messages = (
        UnitMessage.query
        .filter_by(unit_code=unit_code.upper(),
                   channel="assignments",
                   parent_id=None)               # 🔸 filter
        .order_by(UnitMessage.timestamp.asc())
        .all()
    )

    return render_template(
        "unit_chat.html",
        unit_code=unit_code.upper(),
        assignment_messages=assignment_messages,
        current_user=current_user
    )