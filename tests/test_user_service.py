"""Tests for the UserService class."""

import pytest
import mongomock
from unittest.mock import patch
from bson import ObjectId
from app import create_app
from app.extensions import mongo
from app.services.user_service import UserService


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    with patch("flask_pymongo.PyMongo.init_app"):
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        mongo.db = mongomock.MongoClient().db

        yield app


@pytest.fixture
def clean_db(app):
    """Clean the database before each test."""
    with app.app_context():
        mongo.db.users.delete_many({})
    yield


class TestCreateUser:
    """Tests for UserService.create_user()"""

    def test_create_user_success(self, app, clean_db):
        """Test successful user creation."""
        with app.app_context():
            user_id = UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            assert user_id is not None
            assert isinstance(user_id, str)

            # Verify user exists in DB
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            assert user is not None
            assert user["email"] == "test@example.com"
            assert user["first_name"] == "Test"
            assert user["last_name"] == "User"
            assert "password_hash" in user
            assert user["password_hash"] != "password123"  # Should be hashed

    def test_create_user_with_headline(self, app, clean_db):
        """Test user creation with optional headline."""
        with app.app_context():
            user_id = UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
                headline="Software Engineer",
            )

            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            assert user["headline"] == "Software Engineer"

    def test_create_user_stores_created_at(self, app, clean_db):
        """Test that created_at timestamp is stored."""
        with app.app_context():
            user_id = UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            assert "created_at" in user
            assert user["created_at"] is not None


class TestGetUserByEmail:
    """Tests for UserService.get_user_by_email()"""

    def test_get_user_by_email_success(self, app, clean_db):
        """Test retrieving a user by email."""
        with app.app_context():
            # Create user first
            UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user = UserService.get_user_by_email("test@example.com")
            assert user is not None
            assert user.email == "test@example.com"
            assert user.first_name == "Test"
            assert user.last_name == "User"

    def test_get_user_by_email_not_found(self, app, clean_db):
        """Test that None is returned for non-existent email."""
        with app.app_context():
            user = UserService.get_user_by_email("nonexistent@example.com")
            assert user is None


class TestGetUserById:
    """Tests for UserService.get_user_by_id()"""

    def test_get_user_by_id_success(self, app, clean_db):
        """Test retrieving a user by ID."""
        with app.app_context():
            user_id = UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user = UserService.get_user_by_id(user_id)
            assert user is not None
            assert user.email == "test@example.com"

    def test_get_user_by_id_not_found(self, app, clean_db):
        """Test that None is returned for non-existent ID."""
        with app.app_context():
            fake_id = str(ObjectId())
            user = UserService.get_user_by_id(fake_id)
            assert user is None

    def test_get_user_by_id_invalid_id(self, app, clean_db):
        """Test that None is returned for invalid ID format."""
        with app.app_context():
            user = UserService.get_user_by_id("invalid_id")
            assert user is None

    def test_get_user_by_id_none_input(self, app, clean_db):
        """Test that None is returned for None input."""
        with app.app_context():
            user = UserService.get_user_by_id(None)
            assert user is None


class TestVerifyPassword:
    """Tests for UserService.verify_password()"""

    def test_verify_password_correct(self, app, clean_db):
        """Test password verification with correct password."""
        with app.app_context():
            UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user = UserService.get_user_by_email("test@example.com")
            result = UserService.verify_password(user, "password123")
            assert result is True

    def test_verify_password_incorrect(self, app, clean_db):
        """Test password verification with incorrect password."""
        with app.app_context():
            UserService.create_user(
                email="test@example.com",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user = UserService.get_user_by_email("test@example.com")
            result = UserService.verify_password(user, "wrongpassword")
            assert result is False
