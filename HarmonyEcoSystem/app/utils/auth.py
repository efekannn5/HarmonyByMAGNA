from functools import wraps
from typing import Callable

from flask import abort
from flask_login import current_user


def role_required(*roles: str) -> Callable:
    allowed = {role.lower() for role in roles}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            user_role = (current_user.role.Name if current_user.role else "").lower()
            if allowed and user_role not in allowed:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
