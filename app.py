import os
from flask import Flask, jsonify, redirect
from flask_cors import CORS
from flask_smorest import Api
from bcrypt import hashpw, gensalt

from resources.Version import blp as VersionBlueprint

def create_app(settings_module: str = 'globals') -> Flask:
    """
    Creates a new instace of Flask application.
    
    Args:
        settings_module (str, optional): Configuration module to use.
    """
    app = Flask(__name__)
    
    app.config.from_object(settings_module)
        
    CORS(
       app,
       resources={r"/api/*": {"origins": "*"}},
       allow_headers=["Content-Type", "Authorization"],
       supports_credentials=True
    )

    API_TITLE = app.config.get('API_TITLE')
    API_VERSION = app.config.get('API_VERSION')
    SWAGGER_URL = app.config.get('SWAGGER_URL')
    
    app.config['API_TITLE'] = API_TITLE
    app.config['API_VERSION'] = API_VERSION
    app.config['OPENAPI_VERSION'] = '3.0.3'
    app.config['OPENAPI_URL_PREFIX'] = '/'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = SWAGGER_URL
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
        
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

    if not app.config.get("API_KEY"):
        raise ValueError("API_KEY is not set.")
    
    api_key = app.config.get("API_KEY").encode("utf-8")
    hashed = hashpw(api_key, gensalt(rounds=12))
    app.config['API_KEY'] = hashed.decode()
    
    def getApiPrefix(url:str) -> str: return f"{app.config['API_PREFIX']}/{url}"

    api = Api(app)

    # HTTP routes
    api.register_blueprint(VersionBlueprint, url_prefix=app.config['VERSION_ENDPOINT'])
    
    ## NotImplementedError
    @app.errorhandler(NotImplementedError)
    def handle_not_implemented_error(error):
        response = {
            "error_message": str(error),
            "code": 501,
            "status": "Not Implemented"
        }
        return jsonify(response), 501
    
    @app.route('/')
    def main_page():
        """Redirects to the Swagger UI documentation."""
        return redirect(app.config['OPENAPI_SWAGGER_UI_PATH'], code=302)
    
    return app

app = create_app(os.getenv('SETTINGS_MODULE', 'globals'))

if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", port=app.config.get('PORT', 5000), debug=app.config.get('DEBUG', False), use_reloader=app.config.get('DEBUG', False))