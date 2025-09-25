import json
import os
from flask import current_app
from flask_socketio import Namespace
from marshmallow import ValidationError

class SocketEvents(Namespace):
    """Namespace for handling SocketIO events."""

    def on_text_to_speech(self, data):
        """Handle text-to-speech requests."""
        