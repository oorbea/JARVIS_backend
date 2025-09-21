from functools import wraps
from flask import request, jsonify
from helpers.auth.check_secret_key import check_secret_key

def require_api_key():
    """
    Decorator to protect endpoints with x-api-key.
    - 401 if the header is missing.
    - 403 if the key is invalid.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            api_key = request.headers.get('x-api-key')
            if not api_key:
                return jsonify({
                    "error": "Missing API key",
                    "message": "Header 'x-api-key' is required."
                }), 401, {"WWW-Authenticate": "x-api-key realm=\"api\""}

            try:
                if not check_secret_key(api_key):
                    return jsonify({
                        "error": "Forbidden",
                        "message": "Invalid API key."
                    }), 403
            except ValueError as e:
                return jsonify({
                    "error": "Server configuration error",
                    "message": str(e)
                }), 500

            return view_func(*args, **kwargs)
        return wrapped
    return decorator
