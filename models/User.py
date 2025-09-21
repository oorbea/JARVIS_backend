from typing import TypedDict
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

class UserDict(TypedDict):
    email: str
    username: str
    is_admin: bool

class User(db.Model):
    __tablename__ = 'users'
    
    email = db.Column(db.String(120), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(300), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, email: str, username: str, password: str, is_admin: bool = False):
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)
        self.is_admin = is_admin

    def __repr__(self):
        return f"<User {self.username} with email {self.email}>"
    
    def to_dict(self):
        return UserDict(
            email=self.email,
            username=self.username,
            is_admin=self.is_admin
        )
    
    def compare_password(self, password: str) -> bool:
        """
        Compares the given password with the stored hashed password.
        
        Args:
            password (str): The plaintext password to compare.
        
        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return check_password_hash(self.password, password)
    
    def set_password(self, password: str):
        """
        Sets a new password for the user, hashing it before storage.
        
        Args:
            password (str): The new plaintext password.
        """
        self.password = generate_password_hash(password)