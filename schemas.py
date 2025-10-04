from marshmallow import Schema, fields

class UserRegisterSchema(Schema):
    email = fields.Email(required=True, metadata={"description": "The user's email address."})
    password = fields.String(required=True, load_only=True, metadata={"description": "The user's password."})