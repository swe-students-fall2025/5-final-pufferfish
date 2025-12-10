"""
Configuration settings for the application.
"""

import os


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/mydb")
