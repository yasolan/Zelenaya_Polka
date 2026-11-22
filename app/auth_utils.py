from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def nav_visibility():
    guest = not current_user.is_authenticated
    role = None if guest else current_user.role
    return {
        "home": guest or role in ("user", "admin"),
        "catalog": guest or role in ("user", "admin"),
        "zone": guest or role in ("user", "admin"),
        "track": guest or role in ("user", "admin", "picker"),
        "cart": guest or role in ("user", "admin"),
        "addresses": role in ("user", "admin"),
        "picker": role in ("picker", "admin"),
        "courier": role in ("courier", "admin"),
        "admin": role == "admin",
        "login": guest,
        "logout": not guest,
    }
