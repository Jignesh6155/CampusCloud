from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    bio = db.Column(db.Text)
    job_title = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    university = db.Column(db.String(100))  # New field for University
    faculty = db.Column(db.String(100))     # New field for Faculty

    profile_picture = db.Column(db.String(255))  # URL/path to the profile picture
    cover_picture = db.Column(db.String(255))  # URL/path to the cover image
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    def hobbies_list(self):
        """Returns hobbies as a list for Jinja2 templates (if still used)."""
        if self.hobbies:
            return [h.strip() for h in self.hobbies.split(',') if h.strip()]
        return []
