import smtplib
from email.message import EmailMessage

from flask import current_app


def deliver_message(message):
    mail_server = current_app.config.get("MAIL_SERVER")
    if not mail_server:
        return False

    with smtplib.SMTP(
        mail_server,
        current_app.config["MAIL_PORT"],
        timeout=15,
    ) as smtp:
        smtp.ehlo()
        if current_app.config["MAIL_USE_TLS"]:
            smtp.starttls()
            smtp.ehlo()
        username = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    return True


def send_password_reset_email(user, reset_url):
    message = EmailMessage()
    message["Subject"] = "Reset your BloodLink password"
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = user.email
    message.set_content(
        "Hello "
        f"{user.name},\n\nUse this secure link to reset your BloodLink password:\n"
        f"{reset_url}\n\nThis link expires in 30 minutes. If you did not request "
        "a password reset, you can ignore this email.\n"
    )
    sent = deliver_message(message)
    if not sent:
        if current_app.debug or current_app.testing:
            current_app.logger.warning(
                "Development password reset link for %s: %s",
                user.email,
                reset_url,
            )
        else:
            current_app.logger.error("Password reset email skipped: MAIL_SERVER is not set.")
    return sent


def send_verification_otp_email(user, otp):
    message = EmailMessage()
    message["Subject"] = "Verify your BloodLink email"
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = user.email
    message.set_content(
        f"Hello {user.name},\n\nYour BloodLink verification OTP is: {otp}\n\n"
        "This OTP expires in 10 minutes. Do not share it with anyone.\n"
    )
    sent = deliver_message(message)
    if not sent:
        if current_app.debug or current_app.testing:
            current_app.logger.warning(
                "Development email verification OTP for %s: %s",
                user.email,
                otp,
            )
        else:
            current_app.logger.error("Verification email skipped: MAIL_SERVER is not set.")
    return sent
