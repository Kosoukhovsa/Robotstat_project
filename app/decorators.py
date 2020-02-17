from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import UserRoles, Roles


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
# Администратору разрешен полный доступ
            if current_user.is_admin():
                return f(*args, **kwargs)
            user_role = UserRoles.query.filter_by(user=current_user.id, role=Roles.query.filter_by(permissions=permission).first().id).first()
            if user_role is None:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
