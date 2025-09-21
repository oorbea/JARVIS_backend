from flask import current_app as app
from bcrypt import checkpw

def check_api_key(key:str):
    """Check if the provided key matches the API_KEY in the app config."""
    stored_hash:str = app.config.get("API_KEY")
    if not stored_hash:
        raise ValueError("API_KEY is not set in the application configuration.")
    return checkpw(key.encode("utf-8"), stored_hash.encode("utf-8"))