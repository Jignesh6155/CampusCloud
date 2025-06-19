import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import generate_csrf

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()  # ✅ SocketIO initialized

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'w$$a9#^b2av#m2#jQ$s*G831!!6kgY@'

    # Use absolute path for the database file
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, '../instance/app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

    # ✅ Override with test config if provided
    if test_config:
        app.config.update(test_config)

    # ✅ Print the DB URI for confirmation
    print("🚀 Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.index'
    socketio.init_app(app, async_mode='eventlet')  # ✅ SocketIO initialized with async support

    # ✅ Load user for Flask-Login
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ✅ Make CSRF token available in templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    # ✅ Register routes
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app

# ✅ Export these to be used in run.py
__all__ = ['create_app', 'socketio']