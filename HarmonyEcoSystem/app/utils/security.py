from werkzeug.security import generate_password_hash


def hash_password(raw_password: str) -> str:
    return generate_password_hash(raw_password)
