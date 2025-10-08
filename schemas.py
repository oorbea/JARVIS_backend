from marshmallow import Schema, fields, validate
from enums.courtesy_title import CourtesyTitle

class Password(fields.String):
    def __init__(self, *args, **kwargs):
        validators = [
            validate.Length(min=8, error="The password must be at least 8 characters long."),
            validate.Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$',
            error="The password must contain at least one lowercase letter, one uppercase letter, and one number."
            )
        ]
        kwargs.setdefault('validate', validators)
        kwargs.setdefault('load_only', True)
        super().__init__(*args, **kwargs)

class UserRegisterSchema(Schema):
    email = fields.Email(required=True, metadata={"description": "The user's email address."})
    password = Password(required=True, metadata={"description": "The user's password."})
    name = fields.String(required=True, metadata={"description": "The user's first name."})
    surname = fields.String(required=True, metadata={"description": "The user's surname."})
    courtesy_title = fields.Enum(CourtesyTitle, required=True, metadata={"description": "The user's courtesy title."})
    description = fields.String(required=False, allow_none=True, validate=lambda s: len(s) <= 512 if s else True, metadata={"description": "A brief description of the user."})