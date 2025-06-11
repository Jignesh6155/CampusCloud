import pytest
from app import create_app, db
from app.models import User, Post, Comment

@pytest.fixture
def app_context():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

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
    login_user(client, user1.id)

    # Create post with a specific title
    test_title = 'My Custom Title'
    response = client.post('/create-post', data={
        'title': test_title,
        'content': 'Hello world!'
    })
    assert response.status_code == 302

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

 #run using PYTHONPATH=. pytest
 
 
 