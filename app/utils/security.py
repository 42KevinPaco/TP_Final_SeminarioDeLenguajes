"""Password hashing helpers.

Single place that knows how passwords are stored, so swapping the algorithm
later does not touch services or repositories.
"""

from werkzeug.security import check_password_hash, generate_password_hash

MIN_PASSWORD_LENGTH = 4


def hash_password(plain_password: str) -> str:
    """Return a salted hash (scrypt by default in Werkzeug)."""
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compare a plain password against a stored hash."""
    if not plain_password or not password_hash:
        return False
    return check_password_hash(password_hash, plain_password)


def is_password_acceptable(plain_password: str) -> bool:
    return len(plain_password or "") >= MIN_PASSWORD_LENGTH
