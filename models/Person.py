from typing import TypedDict
from db import db
from enums.CourtesyTitle import CourtesyTitle

class PersonDict(TypedDict):
    name: str
    surname: str
    email: str
    courtesy_title: str
    boss: bool
    description: str | None
    can_talk: bool

class Person(db.Model):
    __tablename__ = 'people'

    name = db.Column(db.String(120), primary_key=True)
    surname = db.Column(db.String(120), primary_key=True)
    email = db.Column(db.String(128), db.ForeignKey('users.email'), primary_key=True)
    courtesy_title = db.Column(db.Enum(CourtesyTitle), nullable=False)
    boss = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(512), nullable=True)
    can_talk = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User', backref=db.backref('people', lazy=True))

    def __repr__(self):
        return f"<Person {self.name} {self.surname} of user {self.email}>"

    def to_dict(self) -> PersonDict:
        return PersonDict(
            name=self.name,
            surname=self.surname,
            email=self.email,
            courtesy_title=self.courtesy_title.value,
            boss=self.boss,
            description=self.description,
            can_talk=self.can_talk
        )