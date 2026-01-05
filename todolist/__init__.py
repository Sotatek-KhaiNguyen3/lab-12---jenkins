from flask import Flask
import os
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

db = SQLAlchemy()

load_dotenv()
SECRET_KEY = os.environ.get("KEY")
DB_NAME = os.environ.get("DB_NAME")

def create_database(app):
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', DB_NAME)
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            print(f"Created DB at {db_path}")
    else:
        print(f"Database already exists at {db_path}")

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", DB_NAME)}'

    db.init_app(app)

    from .models import Note, User

    create_database(app)
    from .user import user
    from .views import views
    from .xss_demo import xss as xss_demo

    app.register_blueprint(user)
    app.register_blueprint(views)
    # Mount XSS demo under /xss to keep it isolated from the main app
    app.register_blueprint(xss_demo, url_prefix="/xss")

    login_manager = LoginManager()
    login_manager.login_view = "user.login"
    login_manager.init_app(app)
    app.permanent_session_lifetime = timedelta(minutes=1)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app