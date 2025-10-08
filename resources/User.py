import traceback
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import current_app as app, jsonify
from db import db
from models.Person import Person
from models.User import User

from schemas import UserRegisterSchema

blp = Blueprint('user', __name__, description='User CRUD')

@blp.route('')
class UserEndpoint(MethodView):
    """User endpoints."""

    @blp.arguments(UserRegisterSchema)
    @blp.response(201, description="User successfully registered.")
    @blp.response(400, description="Invalid input data.")
    @blp.response(409, description="User with this email already exists.")
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

            person_payload = {
                "name": data['name'],
                "surname": data['surname'],
                "email": data['email'],
                "courtesy_title": data['courtesy_title'],
                "boss": True,
                "description": data.get('description'),
                "can_talk": True
            }
            person = Person(**person_payload)
            db.session.add(person)

            db.session.commit()

            return_payload = {
                "user": user.to_dict(),
                "person": person.to_dict()
            }
            return jsonify(return_payload), 201
        except ValueError as e:
            db.session.rollback()
            abort(400, message=str(e))
        except db.IntegrityError as e:
            db.session.rollback()
            abort(409, message="User with this email already exists.")
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            abort(500, message=str(e))

@blp.route('/login')
class LoginEndpoint(MethodView):
    """User login endpoint."""

    @blp.arguments(UserRegisterSchema(only=("email", "password")))
    @blp.response(200, description="User successfully logged in.")
    @blp.response(400, description="Invalid input data.")
    @blp.response(401, description="Invalid email or password.")
    @blp.response(500, description="Internal Server Error")
    def post(self, data:dict):
        """Login a user."""
        try:
            user:User|None = User.query.get(data['email'])
            if user and user.check_password(data['password']):
                access_token = user.generate_jwt()
                return jsonify({"access_token": access_token}), 200
            else:
                abort(401, message="Invalid email or password.")
        except ValueError as e:
            abort(400, message=str(e))
        except Exception as e:
            traceback.print_exc()
            abort(500, message=str(e))