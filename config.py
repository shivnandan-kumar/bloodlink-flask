import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    ENVIRONMENT = os.environ.get("FLASK_ENV", "development").lower()
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    TESTING = os.environ.get("TESTING", "false").lower() == "true"
    SECRET_KEY = os.environ.get("SECRET_KEY") or (
        "dev-secret-key-change-later"
        if ENVIRONMENT != "production"
        else None
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "bloodlink.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    DOCUMENT_MAX_SIZE = 5 * 1024 * 1024
    RESET_TOKEN_MAX_AGE = 30 * 60
    RESET_TOKEN_SALT = os.environ.get("RESET_TOKEN_SALT", "bloodlink-password-reset")
    EMAIL_OTP_MAX_AGE = 10 * 60
    EMAIL_OTP_RESEND_COOLDOWN = 60
    EMAIL_OTP_MAX_ATTEMPTS = 5
    LOGIN_RATE_LIMIT_ATTEMPTS = int(os.environ.get("LOGIN_RATE_LIMIT_ATTEMPTS", 5))
    LOGIN_RATE_LIMIT_WINDOW = int(os.environ.get("LOGIN_RATE_LIMIT_WINDOW", 15 * 60))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE",
        "true" if ENVIRONMENT == "production" else "false",
    ).lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    PERMANENT_SESSION_LIFETIME = int(
        os.environ.get("PERMANENT_SESSION_LIFETIME", 60 * 60 * 24 * 7)
    )
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "BloodLink <no-reply@bloodlink.local>",
    )
    DEFAULT_ADMIN_NAME = os.environ.get("DEFAULT_ADMIN_NAME", "BloodLink Admin")
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_CITY = os.environ.get("DEFAULT_ADMIN_CITY", "Ranchi")
    DEFAULT_ADMIN_PINCODE = os.environ.get("DEFAULT_ADMIN_PINCODE")
    DEFAULT_ADMIN_BLOOD_GROUP = os.environ.get("DEFAULT_ADMIN_BLOOD_GROUP", "O+")

    @classmethod
    def validate_for_startup(cls):
        if cls.ENVIRONMENT != "production":
            return

        missing = []
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-secret-key-change-later":
            missing.append("SECRET_KEY")
        if not os.environ.get("DATABASE_URL"):
            missing.append("DATABASE_URL")
        if not os.environ.get("RESET_TOKEN_SALT"):
            missing.append("RESET_TOKEN_SALT")
        if cls.DEBUG:
            missing.append("DEBUG must be false in production")
        if missing:
            raise RuntimeError(
                "Production security configuration is incomplete: "
                + ", ".join(missing)
            )
