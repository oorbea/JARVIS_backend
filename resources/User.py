import traceback
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import Response, current_app as app, jsonify
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
            traceback.print_exc()
            db.session.rollback()
            abort(400, message=str(e))
        except db.IntegrityError as e:
            traceback.print_exc()
            db.session.rollback()
            abort(409, message="User with this email already exists.")
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            abort(500, message=str(e))
    
    @jwt_required()
    @blp.response(200, description="My user information retrieved successfully.")
    @blp.response(401, description="Missing or invalid JWT.")
    @blp.response(404, description="User not found.")
    @blp.response(500, description="Internal Server Error")
    def get(self):
        """Get my user information."""
        try:
            email:str = get_jwt_identity()
            user:User|None = User.query.get(email)
            if not user:
                abort(404, message="User not found.")
            return jsonify(user.to_dict()), 200
        except Exception as e:
            traceback.print_exc()
            abort(500, message=str(e))

    @jwt_required()
    @blp.arguments(UserRegisterSchema(only=("email", "password")))
    @blp.response(200, description="My user information updated successfully.")
    @blp.response(400, description="Invalid input data.")
    @blp.response(401, description="Missing or invalid JWT.")
    @blp.response(404, description="User not found.")
    @blp.response(409, description="User with this email already exists.")
    @blp.response(500, description="Internal Server Error")
    def put(self, data:dict):
        """Update my user information."""
        try:
            email:str = get_jwt_identity()
            user:User|None = User.query.get(email)
            if not user:
                abort(404, message="User not found.")
            new_user:User|None = User.query.get(data['email'])
            if new_user and new_user.email != user.email:
                abort(409, message="User with this email already exists.")
            user.password = User.hash_password(data['password'])
            user.email = data['email']
            db.session.commit()
            return jsonify(user.to_dict()), 200
        except ValueError as e:
            traceback.print_exc()
            db.session.rollback()
            abort(400, message=str(e))
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            abort(500, message=str(e))

    @jwt_required()
    @blp.arguments(UserRegisterSchema(partial=True, only=("email", "password")))
    @blp.response(200, description="My user information updated successfully.")
    @blp.response(400, description="Invalid input data.")
    @blp.response(401, description="Missing or invalid JWT.")
    @blp.response(404, description="User not found.")
    @blp.response(409, description="User with this email already exists.")
    @blp.response(500, description="Internal Server Error")
    def patch(self, data:dict):
        """Partially update my user information."""
        try:
            email:str = get_jwt_identity()
            user:User|None = User.query.get(email)
            if not user:
                abort(404, message="User not found.")
            if 'email' in data:
                new_user:User|None = User.query.get(data['email'])
                if new_user and new_user.email != user.email:
                    abort(409, message="User with this email already exists.")
                user.email = data['email']
            if 'password' in data:
                user.password = User.hash_password(data['password'])
            db.session.commit()
            return jsonify(user.to_dict()), 200
        except ValueError as e:
            traceback.print_exc()
            db.session.rollback()
            abort(400, message=str(e))
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            abort(500, message=str(e))

    @jwt_required()
    @blp.response(204, description="User successfully deleted.")
    @blp.response(401, description="Missing or invalid JWT.")
    @blp.response(404, description="User not found.")
    @blp.response(500, description="Internal Server Error")
    def delete(self):
        """Delete my user account."""
        try:
            email:str = get_jwt_identity()
            user:User|None = User.query.get(email)
            if not user:
                abort(404, message="User not found.")
            db.session.delete(user)
            db.session.commit()
            return Response(status=204)
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
            traceback.print_exc()
            abort(400, message=str(e))
        except Exception as e:
            traceback.print_exc()
            abort(500, message=str(e))