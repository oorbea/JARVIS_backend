from typing import TypedDict
from db import db

class VoiceSampleDict(TypedDict):
    id: int
    name: str
    surname: str
    email: str
    sample: bytes

class VoiceSample(db.Model):
    __tablename__ = 'voice_samples'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), db.ForeignKey('people.name'))
    surname = db.Column(db.String(120), db.ForeignKey('people.surname'))
    email = db.Column(db.String(128), db.ForeignKey('people.email'))
    sample = db.Column(db.LargeBinary, nullable=False)
    person = db.relationship('Person', backref=db.backref('voice_samples', lazy=True))

    def __repr__(self):
        return f"<VoiceSample  {self.id} of person {self.name} {self.surname} ({self.email})>"

    def to_dict(self) -> VoiceSampleDict:
        return VoiceSampleDict(
            id=self.id,
            name=self.name,
            surname=self.surname,
            email=self.email,
            sample=self.sample
        )