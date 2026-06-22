import smtplib
from email.message import EmailMessage

from flask import current_app


def send_password_reset_email(user, reset_url):
    mail_server = current_app.config.get("MAIL_SERVER")
    if not mail_server:
        if current_app.debug or current_app.testing:
            current_app.logger.warning(
                "Development password reset link for %s: %s",
                user.email,
                reset_url,
            )
        else:
            current_app.logger.error("Password reset email skipped: MAIL_SERVER is not set.")
        return False

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
