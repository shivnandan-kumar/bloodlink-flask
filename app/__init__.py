import click
from flask import Flask, render_template
from flask_login import current_user

from config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.routes import main
    from app.auth import auth
    from app.models import Notification, User
    from app.donor import donor
    from app.blood_requests import blood_request
    from app.admin import admin
    from app.notifications import notifications
    from app.donations import donation

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(donor)
    app.register_blueprint(blood_request)
    app.register_blueprint(admin)
    app.register_blueprint(notifications)
    app.register_blueprint(donation)

    @app.context_processor
    def notification_context():
        if not current_user.is_authenticated:
            return {"unread_notification_count": 0}
        unread_count = db.session.scalar(
            db.select(db.func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
        return {"unread_notification_count": unread_count}

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

    @app.cli.command("create-default-admin")
    def create_default_admin():
        """Create or restore the default admin account from environment values."""
        admin_email = (app.config.get("DEFAULT_ADMIN_EMAIL") or "").strip().lower()
        admin_password = app.config.get("DEFAULT_ADMIN_PASSWORD") or ""
        admin_name = (app.config.get("DEFAULT_ADMIN_NAME") or "BloodLink Admin").strip()
        admin_city = (app.config.get("DEFAULT_ADMIN_CITY") or "Ranchi").strip()
        admin_blood_group = (
            app.config.get("DEFAULT_ADMIN_BLOOD_GROUP") or "O+"
        ).strip().upper()

        if not admin_email:
            raise click.ClickException("DEFAULT_ADMIN_EMAIL is missing in .env.")
        if not admin_password:
            raise click.ClickException("DEFAULT_ADMIN_PASSWORD is missing in .env.")
        if len(admin_password) < 8:
            raise click.ClickException(
                "DEFAULT_ADMIN_PASSWORD must be at least 8 characters."
            )

        user = db.session.scalar(db.select(User).where(User.email == admin_email))
        if user:
            changed = False
            if not user.is_admin:
                user.is_admin = True
                changed = True
            if not user.is_email_verified:
                user.is_email_verified = True
                changed = True
            if changed:
                db.session.commit()
                click.echo(f"Default admin restored for {user.email}.")
            else:
                click.echo(f"Default admin already exists: {user.email}.")
            return

        user = User(
            name=admin_name,
            email=admin_email,
            city=admin_city,
            blood_group=admin_blood_group,
            is_admin=True,
            is_email_verified=True,
        )
        user.set_password(admin_password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Default admin created: {user.email}.")

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    @app.errorhandler(413)
    def file_too_large(error):
        return render_template("413.html"), 413

    return app
