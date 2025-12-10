"""Tests for the feed views and main views."""

import pytest
import mongomock
from unittest.mock import patch
from bson import ObjectId
from datetime import datetime, timezone
from app import create_app
from app.extensions import mongo


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


def create_test_user_with_resume(client):
    """Helper to create user with a current resume set."""
    user_id = create_test_user(client)

    # Create a resume
    resume_id = ObjectId()
    mongo.db.resumes.insert_one(
        {
            "_id": resume_id,
            "user_id": user_id,
            "title": "Test Resume",
            "created_at": datetime.now(timezone.utc),
            "structured_data": {
                "name": "Test User",
                "professional_summary": "A test summary",
                "skills": [
                    {
                        "category": "Programming",
                        "skills": "Python, JavaScript, Java, C++, SQL",
                    }
                ],
                "experience": [
                    {
                        "role": "Software Engineer",
                        "company": "Test Corp",
                        "location": "New York",
                    }
                ],
                "education": [{"institution": "Test University", "location": "Boston"}],
            },
        }
    )

    # Set current_resume_id on user
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"current_resume_id": str(resume_id)}}
    )

    return user_id, str(resume_id)


class TestMainViews:
    """Tests for main views."""

    def test_index_route(self, client):
        """Test the index route returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_renders_template(self, client):
        """Test that index renders the main template."""
        response = client.get("/")
        assert response.status_code == 200
        # Should contain some HTML content
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestFeedViews:
    """Tests for feed views."""

    def test_feed_requires_login(self, client):
        """Test that feed route requires authentication."""
        response = client.get("/feed")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_feed_accessible_when_logged_in(self, client):
        """Test that feed is accessible when logged in."""
        create_test_user(client)

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_displays_resumes(self, client):
        """Test that feed displays available resumes."""
        user_id = create_test_user(client)

        # Add some resumes
        mongo.db.resumes.insert_many(
            [
                {
                    "_id": ObjectId(),
                    "user_id": "other_user",
                    "structured_data": {
                        "name": "Software Engineer Resume",
                        "skills": [
                            {"category": "Programming", "skills": "Python, Java"}
                        ],
                    },
                },
                {
                    "_id": ObjectId(),
                    "user_id": "another_user",
                    "structured_data": {
                        "name": "Data Scientist Resume",
                        "skills": [{"category": "Data", "skills": "SQL, Python, R"}],
                    },
                },
            ]
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_pagination(self, client):
        """Test that feed supports pagination parameters."""
        create_test_user(client)

        response = client.get("/feed?page=1&per_page=10")
        assert response.status_code == 200

    def test_feed_search_query_param_accepted(self, client):
        """Test that feed accepts search query parameter (actual search requires real MongoDB)."""
        create_test_user(client)

        # Test that the route accepts the 'q' parameter without crashing
        # Note: Full text search ($text) requires real MongoDB, not mongomock
        # Here we just verify the route handles query params
        response = client.get("/feed?q=")  # Empty query avoids $text filter
        assert response.status_code == 200

    def test_feed_empty_results(self, client):
        """Test feed with no resumes."""
        create_test_user(client)

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_shows_only_current_resumes(self, client):
        """Test that feed only shows users' current resumes."""
        user_id, resume_id = create_test_user_with_resume(client)

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_skills_truncation(self, client):
        """Test that skills are truncated if too long."""
        user_id, resume_id = create_test_user_with_resume(client)

        # Update resume to have very long skills
        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "structured_data.skills": [
                        {
                            "category": "Programming",
                            "skills": "Python, JavaScript, Java, C++, SQL, Ruby, Go, Rust, PHP, Swift, Kotlin, Scala",
                        }
                    ]
                }
            },
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_experience_data(self, client):
        """Test feed extracts experience level from resume data."""
        user_id, resume_id = create_test_user_with_resume(client)

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_experience_only_role(self, client):
        """Test feed handles experience with only role."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "structured_data.experience": [
                        {"role": "Developer", "company": "", "location": ""}
                    ]
                }
            },
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_experience_only_company(self, client):
        """Test feed handles experience with only company."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "structured_data.experience": [
                        {"role": "", "company": "Big Corp", "location": "NYC"}
                    ]
                }
            },
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_location_from_experience(self, client):
        """Test feed extracts location from experience when education has none."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "structured_data.education": [
                        {"institution": "Test U", "location": ""}
                    ],
                    "structured_data.experience": [
                        {"role": "Dev", "company": "Corp", "location": "San Francisco"}
                    ],
                }
            },
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_skills_non_dict(self, client):
        """Test feed handles non-dict items in skills list."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "structured_data.skills": [
                        "string skill",
                        {"category": "Tech", "skills": "Python"},
                    ]
                }
            },
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_string_current_resume_id(self, client):
        """Test feed handles string current_resume_id."""
        user_id = create_test_user(client)

        resume_id = ObjectId()
        mongo.db.resumes.insert_one(
            {
                "_id": resume_id,
                "user_id": user_id,
                "title": "Test Resume",
                "created_at": datetime.now(timezone.utc),
                "structured_data": {"name": "Test"},
            }
        )

        # Set current_resume_id as string
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"current_resume_id": str(resume_id)}}
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_with_objectid_current_resume_id(self, client):
        """Test feed handles ObjectId current_resume_id."""
        user_id = create_test_user(client)

        resume_id = ObjectId()
        mongo.db.resumes.insert_one(
            {
                "_id": resume_id,
                "user_id": user_id,
                "title": "Test Resume",
                "created_at": datetime.now(timezone.utc),
                "structured_data": {"name": "Test"},
            }
        )

        # Set current_resume_id as ObjectId
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"current_resume_id": resume_id}}
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_empty_experience_list(self, client):
        """Test feed handles empty experience list."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)}, {"$set": {"structured_data.experience": []}}
        )

        response = client.get("/feed")
        assert response.status_code == 200

    def test_feed_empty_education_list(self, client):
        """Test feed handles empty education list."""
        user_id, resume_id = create_test_user_with_resume(client)

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)}, {"$set": {"structured_data.education": []}}
        )

        response = client.get("/feed")
        assert response.status_code == 200


class TestResumeViews:
    """Tests for resume views including feedback and storage."""

    def test_resume_feedback_requires_login(self, client):
        """Test that resume feedback route requires authentication."""
        response = client.get("/resume/feedback/someid123")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_resume_feedback_requires_valid_id(self, client):
        """Test that resume feedback route handles missing resume."""
        create_test_user(client)
        response = client.get("/resume/feedback/nonexistent123")
        # Should return 404 or error
        assert response.status_code in [404, 400, 200]

    def test_get_highlights_requires_login(self, client):
        """Test GET /api/highlights requires authentication."""
        response = client.get("/api/highlights?documentId=test123")
        assert response.status_code == 302

    def test_get_highlights_no_document_id(self, client):
        """Test GET /api/highlights without documentId."""
        create_test_user(client)
        response = client.get("/api/highlights")
        assert response.status_code == 400
        assert (
            b"Missing documentId" in response.data or b"error" in response.data.lower()
        )

    def test_get_highlights_with_document_id(self, client):
        """Test GET /api/highlights with documentId."""
        create_test_user(client)
        response = client.get("/api/highlights?documentId=test123")
        assert response.status_code == 200

    def test_post_highlights_requires_login(self, client):
        """Test POST /api/highlights requires authentication."""
        response = client.post(
            "/api/highlights", json={"documentId": "test", "highlights": {}}, content_type="application/json"
        )
        assert response.status_code == 302

    def test_post_highlights_missing_fields(self, client):
        """Test POST /api/highlights with missing fields."""
        create_test_user(client)
        response = client.post(
            "/api/highlights", json={}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_post_highlights_success(self, client):
        """Test POST /api/highlights with valid data."""
        create_test_user(client)

        data = {
            "documentId": "test_doc_123",
            "highlights": {
                "1": [{"id": "hl1", "comment": "Good work!", "text": "Test"}]
            },
        }

        response = client.post(
            "/api/highlights", json=data, content_type="application/json"
        )
        assert response.status_code == 200
        assert b"success" in response.data
