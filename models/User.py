from typing import TypedDict
from db import db

class UserDict(TypedDict):
    email: str
    password: str

class User(db.Model):
    __tablename__ = 'users'
    
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<Challenge {self.title}>"
    
    def to_dict(self) -> ChallengeDict:
        return ChallengeDict(
            title=self.title,
            description=self.description,
            drinking=self.drinking,
            sex=self.sex,
            smoking=self.smoking,
            partner_friendly=self.partner_friendly,
            probability=self.probability,
            icon=self.icon,
            skipping=self.skipping,
            voting=self.voting,
            prize=self.prize,
            males=self.males,
            females=self.females
        )

    def __len__(self) -> int:
        """
        Returns the length of the challenge description.
        """
        return len(self.description)