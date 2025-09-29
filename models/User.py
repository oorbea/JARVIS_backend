from typing import TypedDict
from db import db
import bcrypt

class UserDict(TypedDict):
    email: str
    password: str

class User(db.Model):
    __tablename__ = 'users'
    
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self) -> UserDict:
        return UserDict(
            email=self.email,
            password=self.password
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