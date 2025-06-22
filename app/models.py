from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between users and committees
user_committees = db.Table(
    'user_committees',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', name='fk_usercommittees_user_id'), primary_key=True),
    db.Column('committee_id', db.Integer, db.ForeignKey('committees.id', ondelete='CASCADE', name='fk_usercommittees_committee_id'), primary_key=True)
)

# Association table for many-to-many relationship between users and posts (likes)
post_likes = db.Table(
    'post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for follower/following relationships
user_followers = db.Table(
    'user_followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
)

meetup_rsvps = db.Table('meetup_rsvps',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')),
    db.Column('meetup_id', db.Integer, db.ForeignKey('meetups.id', ondelete='CASCADE')),
    db.UniqueConstraint('user_id', 'meetup_id', name='unique_user_meetup_rsvp')
)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100))
    student_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    bio = db.Column(db.Text)
    job_title = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    university = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    major = db.Column(db.String(100))
    quote = db.Column(db.Text)
    skills = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    cover_picture = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())

    committees = db.relationship('Committee', secondary=user_committees, backref='members', lazy='dynamic')
    posts = db.relationship('Post', backref='author', cascade='all, delete-orphan', passive_deletes=True, lazy='dynamic')
    comments = db.relationship('Comment', backref='author', cascade='all, delete-orphan', passive_deletes=True, lazy='dynamic')

    liked_posts = db.relationship('Post', secondary=post_likes, backref=db.backref('likers', lazy='dynamic'))

    followers = db.relationship(
        'User', secondary=user_followers,
        primaryjoin=(user_followers.c.followed_id == id),
        secondaryjoin=(user_followers.c.follower_id == id),
        backref=db.backref('following', lazy='dynamic'),
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} | Student {self.student_number}>'

    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',')] if self.skills else []

    @skills_list.setter
    def skills_list(self, skills_list):
        self.skills = ', '.join(skills_list)

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def campus_followers_count(self):
        my_domain = self.email.split('@')[-1] if self.email else ''
        count = 0
        for follower in self.followers:
            if follower.email and follower.email.split('@')[-1] == my_domain:
                count += 1
        return count


class Committee(db.Model):
    __tablename__ = 'committees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Committee {self.name}>'


class Forum(db.Model):
    __tablename__ = 'forums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    normalized_name = db.Column(db.String(100), nullable=False, unique=True)
    university_domain = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    posts = db.relationship('Post', backref='forum', cascade='all, delete-orphan', passive_deletes=True, lazy='dynamic')

    @validates('name')
    def convert_to_lower(self, key, value):
        self.normalized_name = value.lower()
        return value

    def __repr__(self):
        return f'<Forum {self.name}>'


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', name='fk_posts_user_id'), nullable=False)
    committee_id = db.Column(db.Integer, db.ForeignKey('committees.id', ondelete='SET NULL', name='fk_posts_committee_id'), nullable=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id', ondelete='SET NULL', name='fk_posts_forum_id'), nullable=True)

    committee = db.relationship('Committee', backref='posts', lazy='joined')
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', passive_deletes=True, lazy='dynamic')

    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE', name='fk_comments_post_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', name='fk_comments_user_id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE', name='fk_comments_parent_id'), nullable=True)

    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy='joined'
    )

    votes = db.relationship(
        'CommentVote',
        backref='voted_comment',
        cascade='all, delete-orphan',
        passive_deletes=True,
        overlaps="comment_votes,voted_comment"
    )

    @property
    def score(self):
        return sum(vote.vote for vote in self.votes)

    def user_vote(self, user_id):
        for vote in self.votes:
            if vote.user_id == user_id:
                return vote.vote
        return 0

    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}>'


class CommentVote(db.Model):
    __tablename__ = 'comment_votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    vote = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),
    )

    user = db.relationship('User', backref='comment_votes')
    comment = db.relationship('Comment', backref='comment_votes', overlaps="votes,voted_comment")

    def __repr__(self):
        return f'<CommentVote User {self.user_id} on Comment {self.comment_id} | Vote {self.vote}>'

class UnitMessage(db.Model):
    __tablename__ = "unit_messages"

    id        = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(20), nullable=False)
    channel   = db.Column(db.String(20), nullable=False, default="general")
    message   = db.Column(db.Text,       nullable=False)

    author    = db.Column(db.String(100), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = db.Column(db.DateTime, default=db.func.now())

    # 🔹 NEW — thread support
    parent_id = db.Column(db.Integer,
                          db.ForeignKey("unit_messages.id", ondelete="CASCADE"),
                          nullable=True)
    replies   = db.relationship(
        "UnitMessage",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )

    user = db.relationship("User", backref="unit_messages")

    def __repr__(self):
        return f"<UnitMessage #{self.id} in {self.unit_code}/{self.channel}>"
    
    
class Meetup(db.Model):
    __tablename__ = 'meetups'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    time = db.Column(db.DateTime)
    rsvp_count = db.Column(db.Integer, default=0)
    type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.now())
    university = db.Column(db.String(100), nullable=False)
    anonymous = db.Column(db.Boolean, default=False)



    unit_code = db.Column(db.String(20), nullable=True)  # ✅ Optional Unit Code

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user = db.relationship('User', backref='meetups')

    rsvped_users = db.relationship(
        'User',
        secondary=meetup_rsvps,
        backref='rsvped_meetups'
    )