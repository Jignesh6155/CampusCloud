# app/__init__.py
import os
import stripe  # ✅ Required for stripe.api_key
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import generate_csrf
from dotenv import load_dotenv  # ✅ Required to load .env variables

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

def create_app(test_config=None):
    # ✅ Load .env variables before doing anything else
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

    # ✅ Set Stripe API key from environment
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, '../instance/app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

    if test_config:
        app.config.update(test_config)

    print("🚀 Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    login_manager.login_view = 'routes.index'

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
