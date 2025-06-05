from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

user_committees = db.Table(
    'user_committees',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('committee_id', db.Integer, db.ForeignKey('committees.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    bio = db.Column(db.Text)
    job_title = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    university = db.Column(db.String(100))  
    faculty = db.Column(db.String(100))    
    major = db.Column(db.String(100))      
    student_number = db.Column(db.String(50))  
    motivational_quote = db.Column(db.Text)  
    profile_picture = db.Column(db.String(255))  
    cover_picture = db.Column(db.String(255))    
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Many-to-many relationship to committees
    committees = db.relationship('Committee', secondary=user_committees, backref='members', lazy='dynamic')

    # One-to-many
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Committee(db.Model):
    __tablename__ = 'committees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Committee {self.name}>'

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    committee_id = db.Column(db.Integer, db.ForeignKey('committees.id'), nullable=True)
    committee = db.relationship('Committee', backref='posts', lazy='joined')

    # One-to-many
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)

    # User who authored the comment
    author = db.relationship('User', backref='authored_comments')

    # Replies for threaded comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}>'
