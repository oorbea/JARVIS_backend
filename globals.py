import os
from dotenv import load_dotenv

VERSION = '0.0.1'

DEFAULT_VERSION_ENDPOINT = '/api/version'

DEFAULT_API_PREFIX = '/api/v1'
DEFAULT_API_TITLE = 'J.A.R.V.I.S. API'
DEFAULT_SWAGGER_URL = '/api-docs'
DEFAULT_DEBUG = False
DEFAULT_PORT = 5000

#------------------------------

load_dotenv()

VERSION_ENDPOINT = os.getenv('VERSION_ENDPOINT', DEFAULT_VERSION_ENDPOINT)
API_PREFIX=os.getenv('API_PREFIX', DEFAULT_API_PREFIX)
API_TITLE=os.getenv('API_TITLE', DEFAULT_API_TITLE)
API_VERSION=os.getenv('API_VERSION', VERSION)
SWAGGER_URL=os.getenv('SWAGGER_URL', DEFAULT_SWAGGER_URL)
DEBUG = str(os.getenv('DEBUG', DEFAULT_DEBUG)).lower() in ('t', 'true', '1', 'y', 'yes')
PORT = int(os.getenv('PORT', DEFAULT_PORT))
HOST_NAME = os.getenv('HOST_NAME', f'http://localhost:{PORT}')
API_KEY = os.getenv('API_KEY', None)

#------------------------------

MURF_API_KEY = os.getenv("MURF_API_KEY")