import json
import os
from flask import current_app
from flask_socketio import Namespace, join_room, leave_room
from marshmallow import ValidationError

class SocketEvents(Namespace):
    """Namespace for handling SocketIO events."""

    pass