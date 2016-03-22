# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED     = True

CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"