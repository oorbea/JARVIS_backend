from dataclasses import dataclass

from enums.CourtesyTitle import CourtesyTitle

@dataclass
class Person:
    name: str
    surname: str
    title: CourtesyTitle
    description: str = ""
    boss: bool = False