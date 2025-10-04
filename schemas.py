from marshmallow import Schema, fields
from enums.CourtesyTitle import CourtesyTitle

class UserRegisterSchema(Schema):
    email = fields.Email(required=True, metadata={"description": "The user's email address."})
    password = fields.String(required=True, load_only=True, metadata={"description": "The user's password."})
    name = fields.String(required=True, metadata={"description": "The user's first name."})
    surname = fields.String(required=True, metadata={"description": "The user's surname."})
    courtesy_title = fields.Enum(CourtesyTitle, required=True, metadata={"description": "The user's courtesy title."})
    description = fields.String(required=False, allow_none=True, validate=lambda s: len(s) <= 512 if s else True, metadata={"description": "A brief description of the user."})