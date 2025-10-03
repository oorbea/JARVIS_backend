from typing import TypedDict
from db import db
import bcrypt
from flask_jwt_extended import create_access_token
import datetime

class UserDict(TypedDict):
    email: str
    password: str
    admin: bool

class User(db.Model):
    __tablename__ = 'users'
    
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(128), nullable=False)
    admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self) -> UserDict:
        return UserDict(
            email=self.email,
            password=self.password,
            admin=self.admin
        )
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password
        
        Args:
            password (str): The password to hash
            
        Returns:
            str: The hashed password
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """
        Check a password against the stored hash
        
        Args:
            password (str): The password to check

        Returns:
            bool: True if the password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def generate_jwt(self) -> str:
        """
        Generate a JWT for the user
        
        Returns:
            str: The generated JWT
        """
        expires = datetime.timedelta(weeks=4)
        return create_access_token(identity=self.email, expires_delta=expires)