import smtplib

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS
from app.email_verification import (
    create_email_otp,
    mark_email_verified,
    resend_wait_seconds,
    verify_email_otp,
)
from app.extensions import db
from app.mailer import send_password_reset_email, send_verification_otp_email
from app.models import User
from app.password_reset import generate_reset_token, verify_reset_token
from app.security import (
    clear_failed_logins,
    is_login_rate_limited,
    login_rate_limit_key,
    password_strength_errors,
    record_failed_login,
)


auth = Blueprint("auth", __name__)


def send_email_otp_safely(user, otp):
    try:
        return send_verification_otp_email(user, otp)
    except (OSError, smtplib.SMTPException):
        current_app.logger.exception("Email verification OTP could not be sent.")
        return False


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        city = request.form.get("city", "").strip()
        pincode = "".join(
            character
            for character in request.form.get("pincode", "").strip()
            if character.isdigit()
        )
        blood_group = request.form.get("blood_group", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        password_errors = password_strength_errors(password)
        existing_user = db.session.scalar(
            db.select(User).where(User.email == email)
        )

        if not all((name, email, city, pincode, blood_group, password, confirm_password)):
            flash("Please fill in all fields.", "danger")
        elif "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "danger")
        elif len(pincode) != 6:
            flash("Please enter a valid 6-digit pincode.", "danger")
        elif blood_group not in BLOOD_GROUPS:
            flash("Please select a valid blood group.", "danger")
        elif password_errors:
            for error in password_errors:
                flash(error, "danger")
        elif password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
        elif existing_user:
            message = (
                "Registration is pending for this email. Login to continue verification."
                if not existing_user.is_email_verified
                else "This email is already registered."
            )
            flash(message, "warning")
        else:
            user = User(
                name=name,
                email=email,
                city=city,
                pincode=pincode,
                blood_group=blood_group,
                is_email_verified=False,
            )
            user.set_password(password)
            otp = create_email_otp(user)
            try:
                db.session.add(user)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Registration could not be completed. Please try again.", "danger")
                return render_template("register.html", blood_groups=BLOOD_GROUPS)

            session["pending_verification_user_id"] = user.id
            if send_email_otp_safely(user, otp):
                flash("A 6-digit verification OTP has been sent to your email.", "success")
            else:
                flash("OTP email could not be sent. Use Resend OTP to try again.", "warning")
            return redirect(url_for("auth.verify_email"))

    return render_template("register.html", blood_groups=BLOOD_GROUPS)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        limit_key = login_rate_limit_key(request.remote_addr, email)
        max_attempts = current_app.config["LOGIN_RATE_LIMIT_ATTEMPTS"]
        window_seconds = current_app.config["LOGIN_RATE_LIMIT_WINDOW"]

        if is_login_rate_limited(limit_key, max_attempts, window_seconds):
            flash("Too many login attempts. Please try again later.", "danger")
            return render_template("login.html"), 429

        user = db.session.scalar(db.select(User).where(User.email == email))

        if user and user.check_password(password):
            if not user.is_email_verified:
                session["pending_verification_user_id"] = user.id
                flash("Verify your email before logging in.", "warning")
                return redirect(url_for("auth.verify_email"))

            clear_failed_logins(limit_key)
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.name}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("main.home"))

        record_failed_login(limit_key, window_seconds)
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user_id = session.get("pending_verification_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user:
        flash("Start registration or login to verify your email.", "warning")
        return redirect(url_for("auth.login"))
    if user.is_email_verified:
        session.pop("pending_verification_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        otp = "".join(
            character
            for character in request.form.get("otp", "").strip()
            if character.isdigit()
        )
        if len(otp) != 6:
            flash("Enter the complete 6-digit OTP.", "danger")
        else:
            verified, error = verify_email_otp(user, otp)
            if verified:
                mark_email_verified(user)
                try:
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    flash("Email verification could not be saved. Try again.", "danger")
                else:
                    session.pop("pending_verification_user_id", None)
                    flash("Email verified successfully. You can now login.", "success")
                    return redirect(url_for("auth.login"))
            else:
                db.session.commit()
                flash(error, "danger")

    return render_template(
        "verify_email.html",
        email=user.email,
        resend_wait=resend_wait_seconds(user),
    )


@auth.route("/verify-email/resend", methods=["POST"])
def resend_email_otp():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user_id = session.get("pending_verification_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user or user.is_email_verified:
        return redirect(url_for("auth.login"))

    wait_seconds = resend_wait_seconds(user)
    if wait_seconds:
        flash(f"Please wait {wait_seconds} seconds before requesting another OTP.", "warning")
        return redirect(url_for("auth.verify_email"))

    otp = create_email_otp(user)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("A new OTP could not be created. Try again.", "danger")
        return redirect(url_for("auth.verify_email"))

    if send_email_otp_safely(user, otp):
        flash("A new verification OTP has been sent.", "success")
    else:
        flash("OTP email could not be sent. Please try again.", "danger")
    return redirect(url_for("auth.verify_email"))


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
        password_errors = password_strength_errors(password)
        if password_errors:
            for error in password_errors:
                flash(error, "danger")
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
