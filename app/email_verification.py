import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_email_otp(user):
    otp = f"{secrets.randbelow(900000) + 100000}"
    now = utc_now_naive()
    user.email_otp_hash = generate_password_hash(otp)
    user.email_otp_sent_at = now
    user.email_otp_expires_at = now + timedelta(
        seconds=current_app.config["EMAIL_OTP_MAX_AGE"]
    )
    user.email_otp_attempts = 0
    return otp


def verify_email_otp(user, submitted_otp):
    if user.email_otp_attempts >= current_app.config["EMAIL_OTP_MAX_ATTEMPTS"]:
        return False, "Too many incorrect attempts. Request a new OTP."
    if not user.email_otp_hash or not user.email_otp_expires_at:
        return False, "Request a new OTP to continue."
    if utc_now_naive() > user.email_otp_expires_at:
        return False, "This OTP has expired. Request a new OTP."

    if not check_password_hash(user.email_otp_hash, submitted_otp):
        user.email_otp_attempts += 1
        remaining = max(
            current_app.config["EMAIL_OTP_MAX_ATTEMPTS"] - user.email_otp_attempts,
            0,
        )
        return False, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining."
    return True, None


def resend_wait_seconds(user):
    if not user.email_otp_sent_at:
        return 0
    elapsed = (utc_now_naive() - user.email_otp_sent_at).total_seconds()
    return max(
        int(current_app.config["EMAIL_OTP_RESEND_COOLDOWN"] - elapsed),
        0,
    )


def mark_email_verified(user):
    user.is_email_verified = True
    user.email_otp_hash = None
    user.email_otp_expires_at = None
    user.email_otp_sent_at = None
    user.email_otp_attempts = 0
