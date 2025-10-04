import traceback
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import current_app as app, jsonify
from db import db
from models.User import User

from schemas import UserRegisterSchema

blp = Blueprint('user', __name__, description='User CRUD')

@blp.route('')
class UserEndpoint(MethodView):
    """User endpoints."""

    @blp.arguments(UserRegisterSchema)
    @blp.response(201, description="User successfully registered.")
    @blp.response(500, description="Internal Server Error")
    def post(self, data:dict):
        """Register a new user."""
        try:
            user_payload = {
                "email": data['email'],
                "password": User.hash_password(data['password']),
                "admin": False
            }
            user = User(**user_payload)
            db.session.add(user)
            db.session.commit()
            return {"message": "User successfully registered."}, 201
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            abort(500, message=str(e))