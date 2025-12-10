"""
Extensions used by the Flask application.
"""

from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

mongo = PyMongo()
login_manager = LoginManager()
bcrypt = Bcrypt()
