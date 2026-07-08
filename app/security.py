import string
import time


SPECIAL_CHARACTERS = set(string.punctuation)
_login_failures = {}


def password_strength_errors(password):
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not any(character.isupper() for character in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(character.isdigit() for character in password):
        errors.append("Password must contain at least one number.")
    if not any(character in SPECIAL_CHARACTERS for character in password):
        errors.append("Password must contain at least one special character.")
    return errors


def login_rate_limit_key(ip_address, email):
    return f"{ip_address or 'unknown'}:{(email or '').strip().lower()}"


def is_login_rate_limited(key, attempts, window_seconds):
    now = time.time()
    failures = [
        timestamp
        for timestamp in _login_failures.get(key, [])
        if now - timestamp < window_seconds
    ]
    _login_failures[key] = failures
    return len(failures) >= attempts


def record_failed_login(key, window_seconds):
    now = time.time()
    failures = [
        timestamp
        for timestamp in _login_failures.get(key, [])
        if now - timestamp < window_seconds
    ]
    failures.append(now)
    _login_failures[key] = failures


def clear_failed_logins(key):
    _login_failures.pop(key, None)
