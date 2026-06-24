import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-later")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "bloodlink.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    DOCUMENT_MAX_SIZE = 5 * 1024 * 1024
    RESET_TOKEN_MAX_AGE = 30 * 60
    EMAIL_OTP_MAX_AGE = 10 * 60
    EMAIL_OTP_RESEND_COOLDOWN = 60
    EMAIL_OTP_MAX_ATTEMPTS = 5
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
    DEFAULT_ADMIN_BLOOD_GROUP = os.environ.get("DEFAULT_ADMIN_BLOOD_GROUP", "O+")
