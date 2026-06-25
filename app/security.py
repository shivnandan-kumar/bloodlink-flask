import string


SPECIAL_CHARACTERS = set(string.punctuation)


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
