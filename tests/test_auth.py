"""Tests for the auth flow."""

import pytest
import mongomock
from unittest.mock import patch
from app import create_app
from app.extensions import mongo


@pytest.fixture
def client():
    with patch("flask_pymongo.PyMongo.init_app"):
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        mongo.db = mongomock.MongoClient().db

        with app.test_client() as client:
            with app.app_context():
                mongo.db.users.delete_many({})
            yield client


def test_signup_page(client):
    """Test that the signup page loads."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Signup" in response.data


def test_signup_success(client):
    """Test successful user registration."""
    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome to Pufferfish" in response.data

    user = mongo.db.users.find_one({"email": "test@example.com"})
    assert user is not None
    assert user["first_name"] == "Test"


def test_signup_duplicate_email(client):
    """Test signup with existing email."""
    client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "newpassword",
            "first_name": "New",
            "last_name": "User",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Email already registered" in response.data


def test_login_page(client):
    """Test that the login page loads."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_success(client):
    """Test successful login."""
    client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_login_failure(client):
    """Test login with invalid credentials."""
    client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

    response = client.post(
        "/login",
        data={"email": "wrong@example.com", "password": "password123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout(client):
    """Test logout."""
    client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    client.post("/login", data={"email": "test@example.com", "password": "password123"})

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200


def test_protected_route(client):
    """Test access to protected route."""
    response = client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
