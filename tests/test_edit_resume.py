"""Tests for the edit resume functionality."""

import pytest
import mongomock
from unittest.mock import patch, MagicMock
from bson import ObjectId
from app import create_app
from app.extensions import mongo
from app.services.resume_service import ResumeService
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Create and configure a test client."""
    with patch("flask_pymongo.PyMongo.init_app"):
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        mongo.db = mongomock.MongoClient().db

        with app.test_client() as client:
            with app.app_context():
                mongo.db.users.delete_many({})
                mongo.db.resumes.delete_many({})
            yield client


def create_test_user(client):
    """Helper to create and login a test user."""
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

    user = mongo.db.users.find_one({"email": "test@example.com"})
    return str(user["_id"])


def create_resume_for_user(user_id, title="Test Resume", created_at=None):
    """Helper to create a resume doc."""
    doc = {
        "user_id": user_id,
        "title": title,
        "filename": "test.pdf",
        "created_at": created_at or datetime.utcnow(),
        "structured_data": {
            "name": "Test User",
            "email": "test@example.com",
            # Add fields to test prefill
            "professional_summary": "Summary text",
            "education": [
                {"institution": "Test School", "location": "Test City", "degree": "BS"}
            ],
        },
    }
    result = mongo.db.resumes.insert_one(doc)
    return str(result.inserted_id)


class TestEditResume:
    """Tests for editing functionality."""

    def test_edit_route_requires_login(self, client):
        response = client.get("/resume/abc/edit")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_edit_route_loads_data(self, client):
        """Test that the edit form loads with prefilled data."""
        user_id = create_test_user(client)
        resume_id = create_resume_for_user(user_id)

        response = client.get(f"/resume/{resume_id}/edit")
        assert response.status_code == 200
        assert b"Resume submission" in response.data
        # Check prefill data
        assert b"Test Resume" in response.data
        assert b"Test School" in response.data
        assert b"Summary text" in response.data

    def test_edit_route_verify_ownership(self, client):
        """Test cannot edit another user's resume."""
        create_test_user(client)  # User 1

        # Manually create another user and resume
        other_user_id = str(ObjectId())
        other_resume_id = create_resume_for_user(other_user_id)

        response = client.get(f"/resume/{other_resume_id}/edit", follow_redirects=True)
        assert response.status_code == 200
        # Should redirect back or show error, but definitely not show the specific resume data if logic holds
        # Our implementation redirects to /resume-form on error
        assert b"Resume submission" in response.data
        # Should not contain the other user's specific data
        assert b"Test School" not in response.data

    def test_resume_sort_order(self, client):
        """Test that get_user_resumes returns oldest first."""
        user_id = create_test_user(client)

        # Create older resume
        old_time = datetime.utcnow() - timedelta(days=1)
        r1_id = create_resume_for_user(
            user_id, title="Older Resume", created_at=old_time
        )

        # Create newer resume
        new_time = datetime.utcnow()
        r2_id = create_resume_for_user(
            user_id, title="Newer Resume", created_at=new_time
        )

        resumes = ResumeService.get_user_resumes(user_id)
        assert len(resumes) == 2
        # Oldest first (ascending order for horizontal timeline: oldest on left, newest on right)
        assert resumes[0]["_id"] == r1_id
        assert resumes[0]["title"] == "Older Resume"
        assert resumes[1]["_id"] == r2_id
        assert resumes[1]["title"] == "Newer Resume"
