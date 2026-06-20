import click
from flask import Flask, render_template

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
    from app.admin import admin

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(donor)
    app.register_blueprint(blood_request)
    app.register_blueprint(admin)

    @app.cli.command("promote-admin")
    @click.argument("email")
    def promote_admin(email):
        """Promote an existing registered user to admin."""
        user = db.session.scalar(
            db.select(User).where(User.email == email.strip().lower())
        )
        if not user:
            raise click.ClickException("No registered user found with that email.")
        if user.is_admin:
            click.echo(f"{user.email} is already an admin.")
            return

        user.is_admin = True
        db.session.commit()
        click.echo(f"Admin access granted to {user.email}.")

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    return app
