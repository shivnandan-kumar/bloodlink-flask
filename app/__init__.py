from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.routes import main
    from app.auth import auth
    from app.models import User
    from app.donor import donor
    from app.blood_requests import blood_request

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(donor)
    app.register_blueprint(blood_request)

    return app
