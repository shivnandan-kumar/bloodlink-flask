import smtplib

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS
from app.extensions import db
from app.mailer import send_password_reset_email
from app.models import User
from app.password_reset import generate_reset_token, verify_reset_token


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        city = request.form.get("city", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all((name, email, city, blood_group, password, confirm_password)):
            flash("Please fill in all fields.", "danger")
        elif "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "danger")
        elif blood_group not in BLOOD_GROUPS:
            flash("Please select a valid blood group.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
        elif password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
        elif db.session.scalar(db.select(User).where(User.email == email)):
            flash("This email is already registered.", "danger")
        else:
            user = User(
                name=name,
                email=email,
                city=city,
                blood_group=blood_group,
            )
            user.set_password(password)
            try:
                db.session.add(user)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Registration could not be completed. Please try again.", "danger")
                return render_template("register.html", blood_groups=BLOOD_GROUPS)

            flash("Registration successful. Please login.", "success")
            return redirect(url_for("auth.login"))

    return render_template("register.html", blood_groups=BLOOD_GROUPS)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        user = db.session.scalar(db.select(User).where(User.email == email))

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.name}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("main.home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user:
            token = generate_reset_token(user)
            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True,
            )
            try:
                send_password_reset_email(user, reset_url)
            except (OSError, smtplib.SMTPException):
                current_app.logger.exception("Password reset email could not be sent.")

        flash(
            "If that email is registered, a password reset link has been sent.",
            "success",
        )
        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user = verify_reset_token(token)
    if not user:
        flash("This password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
        elif password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
        else:
            user.set_password(password)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Password could not be updated. Please try again.", "danger")
            else:
                flash("Password updated successfully. You can now login.", "success")
                return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))
