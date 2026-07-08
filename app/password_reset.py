import hashlib
import hmac

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db
from app.models import User


def password_fingerprint(user):
    return hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest()[:20]


def generate_reset_token(user):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(
        {
            "user_id": user.id,
            "password": password_fingerprint(user),
        },
        salt=current_app.config["RESET_TOKEN_SALT"],
    )


def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = serializer.loads(
            token,
            salt=current_app.config["RESET_TOKEN_SALT"],
            max_age=current_app.config["RESET_TOKEN_MAX_AGE"],
        )
    except (BadSignature, SignatureExpired):
        return None

    user = db.session.get(User, data.get("user_id"))
    if not user:
        return None
    if not hmac.compare_digest(
        data.get("password", ""),
        password_fingerprint(user),
    ):
        return None
    return user
