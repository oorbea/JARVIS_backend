from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import abort
from models.User import User

def admin_required():
    """
    Decorator that requires the user to be an administrator.
    Should be used together with @jwt_required().
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_identity:str = get_jwt_identity()
            
            user:User = User.query.get(current_user_identity)
            
            if not user:
                abort(401, message="User not found")
            
            if not user.admin:
                abort(403, message="Access denied. Administrator permissions required")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator