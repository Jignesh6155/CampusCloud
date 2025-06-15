import pytest
from app import create_app, db
from sqlalchemy.exc import IntegrityError
from app.models import User, Post, Comment
from app.utils.domain import sanitize_domain
from app.models import Forum

@pytest.fixture
def app_context():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_valid_signup(client):
    response = client.post('/signup', data={
        'student_number': '123456',
        'email': 'test1@student.uwa.edu.au',
        'full_name': 'Test User',
        'password': 'securepassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Account created successfully!' in response.data
    assert User.query.filter_by(email='test1@student.uwa.edu.au').first() is not None

def test_duplicate_email_signup(client):
    # First signup
    client.post('/signup', data={
        'student_number': '123456',
        'email': 'test2@student.uwa.edu.au',
        'full_name': 'Test User',
        'password': 'securepassword'
    })

    # Duplicate signup
    response = client.post('/signup', data={
        'student_number': '654321',  # Different student number
        'email': 'test2@student.uwa.edu.au',  # same email
        'full_name': 'Another User',
        'password': 'anotherpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'An account with that email already exists.' in response.data


def test_signup_missing_fields(client):
    # Missing student number
    response = client.post('/signup', data={
        'student_number': '',
        'email': 'missing@student.uwa.edu.au',
        'full_name': '',
        'password': 'password'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Please fix the errors in the form.' in response.data

def test_signup_invalid_email(client):
    response = client.post('/signup', data={
        'student_number': '987654',
        'email': 'notanemail',
        'full_name': 'Invalid Email User',
        'password': 'password'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Please fix the errors in the form.' in response.data
    
def test_login_with_wrong_email(client, setup_users):
    response = client.post('/login', data={
        'email': 'wrong@uni.edu',
        'password': 'somepassword'
    }, follow_redirects=True)
    assert b'Invalid email or password.' in response.data

def test_login_with_wrong_password(client, setup_users):
    user1, _ = setup_users
    response = client.post('/login', data={
        'email': user1.email,
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email or password.' in response.data

def test_login_with_blank_fields(client):
    response = client.post('/login', data={
        'student_number': '',
        'password': ''
    }, follow_redirects=True)
    assert b'Please fix the errors in the form.' in response.data

@pytest.fixture
def client(app_context):
    return app_context.test_client()

@pytest.fixture
def setup_users():
    user1 = User(student_number='1001', email='user1@uni.edu', password_hash='hash', display_name='User1')
    user2 = User(student_number='1002', email='user2@uni.edu', password_hash='hash', display_name='User2')
    db.session.add_all([user1, user2])
    db.session.commit()
    return user1, user2

def login_user(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)

def test_create_and_delete_post(client, setup_users):
    user1, _ = setup_users
    user1.university = 'uni.edu'  # Required to avoid AttributeError in create_post route
    db.session.commit()

    login_user(client, user1.id)

    # Create post with a specific title
    test_title = 'My Custom Title'
    response = client.post('/create-post', data={
        'title': test_title,
        'content': 'Hello world!'
    })
    assert response.status_code == 302  # Redirect expected

    post = Post.query.first()
    assert post is not None
    assert post.title == test_title
    assert post.content == 'Hello world!'

    # Delete post
    response = client.delete(f'/delete-post/{post.id}')
    data = response.get_json()
    assert data['status'] == 'success'
    assert Post.query.get(post.id) is None

def test_comment_and_reply(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    # Create post
    post = Post(content='Test post', author=user1)
    db.session.add(post)
    db.session.commit()

    # Add comment
    response = client.post(f'/post/{post.id}/comment', json={'content': 'Nice!'})
    data = response.get_json()
    assert data['status'] == 'success'
    comment = Comment.query.first()
    assert comment is not None
    assert comment.content == 'Nice!'

    # Add reply to comment
    response = client.post(f'/comment/{comment.id}/reply', json={'content': 'Thanks!'})
    data = response.get_json()
    assert data['status'] == 'success'
    reply = Comment.query.filter_by(parent_id=comment.id).first()
    assert reply is not None
    assert reply.content == 'Thanks!'

    # Delete comment (should also delete reply)
    response = client.delete(f'/comment/{comment.id}/delete')
    data = response.get_json()
    assert data['status'] == 'success'
    assert Comment.query.count() == 0

def test_like_unlike_post(client, setup_users):
    user1, user2 = setup_users
    login_user(client, user1.id)

    # Create post by user2
    post = Post(content='Like me!', author=user2)
    db.session.add(post)
    db.session.commit()

    # Like post
    response = client.post(f'/like-post/{post.id}')
    data = response.get_json()
    assert data['likes'] == 1
    assert data['liked'] is True

    # Unlike post
    response = client.post(f'/like-post/{post.id}')
    data = response.get_json()
    assert data['likes'] == 0
    assert data['liked'] is False

def test_vote_comment(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    # Create post and comment
    post = Post(content='Vote here', author=user1)
    comment = Comment(content='Vote me', post=post, user_id=user1.id)
    db.session.add_all([post, comment])
    db.session.commit()

    # Upvote
    response = client.post(f'/comment/{comment.id}/vote', json={'vote': 1})
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['new_score'] == 1
    assert data['user_vote'] == 1

    # Downvote (should override upvote)
    response = client.post(f'/comment/{comment.id}/vote', json={'vote': -1})
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['new_score'] == -1
    assert data['user_vote'] == -1

    # Toggle off (downvote again)
    response = client.post(f'/comment/{comment.id}/vote', json={'vote': -1})
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['new_score'] == 0
    assert data['user_vote'] == 0

def test_api_search_users(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    # Search for user by display_name
    response = client.get('/api/search-users?query=User2')
    assert response.status_code == 200
    users = response.get_json()
    assert isinstance(users, list)
    assert any(u['display_name'] == 'User2' for u in users)

def test_update_profile(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    response = client.post('/update-profile', data={
        'display_name': 'New Name',
        'job_title': 'Developer',
        'bio': 'Updated bio!',
        'university': 'Uni A',
        'faculty': 'Engineering',
        'major': 'CS',
        'student_number': user1.student_number,
        'phone': '123456789',
        'quote': 'New quote!',
        'skills': 'Python, Flask'
    }, follow_redirects=True)

    assert response.status_code == 200
    updated_user = User.query.get(user1.id)
    assert updated_user.display_name == 'New Name'
    assert updated_user.bio == 'Updated bio!'
    assert 'Python' in updated_user.skills_list
    assert updated_user.university == 'Uni A'

def test_follow_counts_and_campus_followers(client, app_context):
    # Create users with same domain
    user1 = User(student_number='1', email='u1@uni.edu', password_hash='hash', display_name='U1')
    user2 = User(student_number='2', email='u2@uni.edu', password_hash='hash', display_name='U2')
    user3 = User(student_number='3', email='u3@uni.edu', password_hash='hash', display_name='U3')
    db.session.add_all([user1, user2, user3])
    db.session.commit()

    # Login as user1
    login_user(client, user1.id)

    # Follow user2
    client.post(f'/toggle-follow/{user2.id}')
    db.session.refresh(user2)
    assert user2.followers_count == 1
    assert user2.campus_followers_count == 1

    # Follow user3
    client.post(f'/toggle-follow/{user3.id}')
    db.session.refresh(user3)
    assert user3.followers_count == 1
    assert user3.campus_followers_count == 1

    # Confirm following count for user1
    assert user1.following.count() == 2

def test_following_self_does_not_affect_counts(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    # Try to follow self
    response = client.post(f'/toggle-follow/{user1.id}')
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'You cannot follow yourself.'

    # Counts remain zero
    assert user1.followers_count == 0
    assert user1.campus_followers_count == 0
    
def test_delete_post(client, setup_users):
    """
    Test that a user can delete their post and that it is removed from the database.
    """
    user1, _ = setup_users
    user1.university = 'uni.edu'  # ✅ This line is required
    db.session.commit()

    login_user(client, user1.id)

    # Create a post
    post_title = 'Test Post for Deletion'
    post_content = 'This post will be deleted.'
    response = client.post('/create-post', data={
        'title': post_title,
        'content': post_content
    })

    assert response.status_code == 302  # Redirect after creation

    # Confirm the post exists
    post = Post.query.filter_by(title=post_title).first()
    assert post is not None
    assert post.content == post_content

    # Delete the post
    delete_response = client.delete(f'/delete-post/{post.id}')
    data = delete_response.get_json()

    # Confirm deletion was successful
    assert delete_response.status_code == 200
    assert data['status'] == 'success'

    # Confirm the post is gone from the DB
    deleted_post = Post.query.get(post.id)
    assert deleted_post is None
    
def test_logout(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    response = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out.' in response.data
    
def test_api_user_search_results_redirect_to_profile(client, setup_users):
    user1, user2 = setup_users
    login_user(client, user1.id)

    # Use actual AJAX search route
    response = client.get('/api/search-users?query=User2')
    assert response.status_code == 200

    data = response.get_json()
    assert any(u['display_name'] == 'User2' for u in data)
    
def test_view_other_profile(client, setup_users):
    user1, user2 = setup_users
    login_user(client, user1.id)

    response = client.get(f'/profile/{user2.id}')
    assert response.status_code == 200
    assert user2.display_name.encode() in response.data

def test_edit_profile_page(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    response = client.get('/edit-profile')
    assert response.status_code == 200
    assert b'Edit Profile' in response.data or user1.display_name.encode() in response.data

def test_view_post_thread(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    post = Post(content='View me', author=user1)
    db.session.add(post)
    db.session.commit()

    response = client.get(f'/post/{post.id}')
    assert response.status_code == 200
    assert b'View me' in response.data

def test_signup_creates_forum_if_not_exists(client):
    email = 'newuser@curtin.edu.au'
    response = client.post('/signup', data={
        'student_number': '888888',
        'email': email,
        'full_name': 'Curtin User',
        'password': 'testpass'
    }, follow_redirects=True)

    assert response.status_code == 200

    from app.models import Forum
    forum = Forum.query.filter_by(university_domain='Curtin University').first()

    assert forum is not None
    assert forum.name.lower().startswith('curtin')  # Allow flexibility in casing
    
def test_signup_sanitizes_email_and_creates_forum(client):
    email = 'testuser@student.monash.edu.au'
    client.post('/signup', data={
        'student_number': '20231234',
        'email': email,
        'full_name': 'Monash User',
        'password': 'securepassword'
    }, follow_redirects=True)

    from app.models import Forum
    forum = Forum.query.filter(Forum.university_domain.ilike('%monash%')).first()
    assert forum is not None
    assert forum.name.lower() == 'monash'

def test_post_only_appears_in_specific_forum(client, setup_users):
    user1, _ = setup_users
    user1.email = 'johndoe@student.uwa.edu.au'
    db.session.commit()

    # ✅ Make sure the forum exists for user1's domain
    cleaned_uni = sanitize_domain(user1.email)
    forum = Forum.query.filter_by(university_domain=cleaned_uni).first()
    if not forum:
        forum = Forum(name=cleaned_uni.capitalize(), university_domain=cleaned_uni)
        db.session.add(forum)
        db.session.commit()

    # ✅ Log the user in
    login_user(client, user1.id)

    # ✅ Create a post in that forum
    response = client.post(f'/create-post/{cleaned_uni}', data={
        'title': 'Test Title',
        'content': 'Test content'
    }, follow_redirects=True)

    assert response.status_code == 200

    # ✅ Confirm the post is tied to that forum and not the general one
    from app.models import Post
    posts = Post.query.filter_by(forum_id=forum.id).all()
    assert any(p.title == 'Test Title' for p in posts)
    
def test_cross_uni_post_stays_global(client, setup_users):
    """
    • POST /create-post/general
    • Resulting post has forum_id == None
    """
    user1, _ = setup_users
    user1.email = "alice@student.uwa.edu.au"   # any domain is fine
    db.session.commit()

    login_user(client, user1.id)

    # Create post in the global feed
    title   = "Global Hello"
    content = "This belongs to everyone."
    resp = client.post("/create-post/general", data={
        "title": title,
        "content": content
    }, follow_redirects=True)

    # Should land back on /forum/general
    assert resp.status_code == 200
    assert b"Cross-University Forum" in resp.data or b"GENERAL Forum" in resp.data

    # DB checks
    post = Post.query.filter_by(title=title).first()
    assert post is not None
    assert post.forum_id is None       # ← KEY ASSERTION


def test_global_posts_visible_only_in_general_feed(client, setup_users):
    """
    • Create 1 global post, 1 UWA post
    • /forum/general shows only the global one
    """
    user1, user2 = setup_users
    user1.email = "u1@student.uwa.edu.au"
    user2.email = "u2@student.uwa.edu.au"
    db.session.commit()

    # Ensure UWA forum exists
    from app.utils.domain import sanitize_domain
    domain = sanitize_domain(user1.email)      # "uwa"
    forum   = Forum.query.filter_by(university_domain=domain).first()
    if not forum:
        forum = Forum(name=domain.capitalize(), university_domain=domain)
        db.session.add(forum); db.session.commit()

    # Login as user1 and make a GLOBAL post
    login_user(client, user1.id)
    client.post("/create-post/general", data={
        "title": "Global post",
        "content": "Visible to all"
    })

    # Login as user2 and make a UWA-only post
    login_user(client, user2.id)
    client.post(f"/create-post/{domain}", data={
        "title": "UWA post",
        "content": "Only at UWA"
    })

    # View Cross-University feed
    r = client.get("/forum/general")
    assert r.status_code == 200
    assert b"Global post" in r.data
    assert b"UWA post" not in r.data


def test_unknown_forum_slug_falls_back_to_general(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    r1 = client.get("/forum/nonexistent", follow_redirects=False)
    assert r1.status_code == 302
    # Accept whatever URL the general-forum route generates
    assert r1.location.endswith("/general-forum")

    r2 = client.get(r1.location)
    assert r2.status_code == 200
    assert b"Cross-University Forum" in r2.data or b"GENERAL Forum" in r2.data
    
def test_follow_toggle_consistency(client, setup_users):
    user1, user2 = setup_users
    login_user(client, user1.id)

    r1 = client.post(f'/toggle-follow/{user2.id}')
    r2 = client.post(f'/toggle-follow/{user2.id}')  # Unfollow
    r3 = client.post(f'/toggle-follow/{user2.id}')  # Follow again

    assert r3.status_code == 200
    assert user2.followers_count == 1
    
def test_cannot_delete_others_post(client, setup_users):
    user1, user2 = setup_users
    post = Post(content='user2 post', author=user2)
    db.session.add(post); db.session.commit()

    login_user(client, user1.id)
    r = client.delete(f'/delete-post/{post.id}')
    assert r.status_code == 403  # Or 404 depending on implementation

def test_forum_name_duplicate_case_insensitive(app_context):
    # Create initial forum
    forum1 = Forum(name='Curtin', university_domain='curtin.edu.au', normalized_name='curtin')
    db.session.add(forum1)
    db.session.commit()

    # Try adding a case-variant duplicate
    forum2 = Forum(name='CURTIN', university_domain='curtin.edu', normalized_name='curtin')
    db.session.add(forum2)

    with pytest.raises(IntegrityError):
        db.session.commit()
        
def test_known_slug_forum_renders(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    forum = Forum(name="Curtin", university_domain="curtin.edu.au", normalized_name="curtin")
    db.session.add(forum); db.session.commit()

    response = client.get('/forum/curtin')
    assert response.status_code == 200
    assert b"Curtin" in response.data
    
def test_cross_university_alias_works(client, setup_users):
    user1, _ = setup_users
    login_user(client, user1.id)

    response = client.get('/forum/cross-university')
    assert response.status_code == 200
    assert b"Cross-University Forum" in response.data or b"GENERAL Forum" in response.data
    


 #run using PYTHONPATH=. pytest
 #PYTHONPATH=. pytest -v
 #PYTHONPATH=. pytest -v -p no:warnings


 
 
 
 