from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'yoursecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register routes as a Blueprint
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
