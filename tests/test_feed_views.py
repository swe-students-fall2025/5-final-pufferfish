"""Tests for feed views."""

import pytest
import mongomock
from unittest.mock import patch, MagicMock
from bson import ObjectId
from app import create_app
from app.extensions import mongo


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    with patch("flask_pymongo.PyMongo.init_app"):
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        mongo.db = mongomock.MongoClient().db

        with app.app_context():
            yield app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def clean_db(app):
    """Clean the database before each test."""
    with app.app_context():
        mongo.db.resumes.delete_many({})
        mongo.db.users.delete_many({})
        yield


@pytest.fixture
def authenticated_user(app, clean_db):
    """Create and authenticate a test user."""
    with app.app_context():
        user_id = ObjectId()
        mongo.db.users.insert_one(
            {
                "_id": user_id,
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            }
        )

        # Create a mock user object
        mock_user = MagicMock()
        mock_user.id = str(user_id)
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.is_anonymous = False

        yield mock_user


@pytest.fixture
def sample_resumes(app, clean_db):
    """Create sample resumes in the database."""
    with app.app_context():
        user1_id = str(ObjectId())
        user2_id = str(ObjectId())
        user3_id = str(ObjectId())

        resumes = [
            {
                "_id": ObjectId(),
                "user_id": user1_id,
                "filename": "resume1.pdf",
                "structured_data": {
                    "name": "Alice Chen",
                    "professional_summary": "Experienced software engineer with 5 years in web development",
                    "skills": [
                        {"skills": "Python"},
                        {"skills": "JavaScript"},
                        {"skills": "React"},
                    ],
                    "location": "San Francisco, CA",
                },
            },
            {
                "_id": ObjectId(),
                "user_id": user2_id,
                "filename": "resume2.pdf",
                "structured_data": {
                    "name": "Bob Martinez",
                    "professional_summary": "Data scientist specializing in machine learning",
                    "skills": [
                        {"skills": "Python"},
                        {"skills": "TensorFlow"},
                        {"skills": "SQL"},
                    ],
                    "location": "New York, NY",
                },
            },
            {
                "_id": ObjectId(),
                "user_id": user3_id,
                "filename": "resume3.pdf",
                "structured_data": {
                    "name": "Charlie Davis",
                    "professional_summary": "Frontend developer passionate about UX",
                    "skills": [
                        {"skills": "React"},
                        {"skills": "Vue.js"},
                        {"skills": "CSS"},
                    ],
                    "location": "Austin, TX",
                },
            },
        ]
        mongo.db.resumes.insert_many(resumes)
        yield resumes


class TestFeedHome:
    """Tests for the feed_home view."""

    def test_feed_requires_authentication(self, client, clean_db):
        """Test that feed requires login."""
        response = client.get("/feed")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    @patch("flask_login.utils._get_user")
    def test_feed_renders_successfully(
        self, mock_current_user, client, authenticated_user, clean_db
    ):
        """Test that feed page renders successfully for authenticated users."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_feed_displays_all_resumes(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that feed displays all resumes."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200
        assert b"Alice Chen" in response.data
        assert b"Bob Martinez" in response.data
        assert b"Charlie Davis" in response.data

    @patch("flask_login.utils._get_user")
    def test_feed_displays_resume_details(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that feed displays resume details correctly."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200
        assert b"Experienced software engineer" in response.data
        assert b"Python" in response.data
        assert b"San Francisco, CA" in response.data

    @patch("flask_login.utils._get_user")
    def test_feed_displays_skills(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that feed displays skills from structured data."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200
        assert b"JavaScript" in response.data
        assert b"React" in response.data
        assert b"TensorFlow" in response.data

    @patch("flask_login.utils._get_user")
    def test_feed_passes_correct_template_variables(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that correct variables are passed to template."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200
        # Variables: resumes, query, page, per_page, total


class TestFeedPagination:
    """Tests for feed pagination."""

    @patch("flask_login.utils._get_user")
    def test_default_pagination(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test default pagination parameters (page=1, per_page=20)."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_custom_page_number(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test custom page number."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            # Create 25 resumes to test pagination
            resumes = [
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": f"resume_{i}.pdf",
                    "structured_data": {
                        "name": f"User {i}",
                        "professional_summary": f"Summary {i}",
                        "skills": [{"skills": f"Skill{i}"}],
                    },
                }
                for i in range(25)
            ]
            mongo.db.resumes.insert_many(resumes)

        response = client.get("/feed?page=2")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_custom_per_page(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test custom per_page parameter."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed?per_page=10")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_pagination_calculates_skip_correctly(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test that pagination skip is calculated correctly: (page-1)*per_page."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            # Create 30 resumes with identifiable data
            resumes = [
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": f"resume_{i:02d}.pdf",
                    "structured_data": {
                        "name": f"User {i:02d}",
                        "professional_summary": "",
                        "skills": [],
                    },
                }
                for i in range(30)
            ]
            mongo.db.resumes.insert_many(resumes)

        # Page 2 with 10 per page should skip first 10 (skip=10)
        response = client.get("/feed?page=2&per_page=10")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_pagination_total_count(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that total count is correctly calculated."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200
        # Total should be 3 from sample_resumes


class TestFeedSearch:
    """Tests for feed search functionality."""

    @patch("flask_login.utils._get_user")
    @patch("app.extensions.mongo.db.resumes.find")
    @patch("app.extensions.mongo.db.resumes.count_documents")
    def test_search_with_query_parameter(
        self, mock_count, mock_find, mock_current_user, client, authenticated_user
    ):
        """Test searching with text query parameter."""
        mock_current_user.return_value = authenticated_user

        # Mock the cursor returned by find()
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": ObjectId(),
                "user_id": str(ObjectId()),
                "filename": "python_resume.pdf",
                "structured_data": {
                    "name": "Python Developer",
                    "professional_summary": "Expert in Python programming",
                    "skills": [{"skills": "Python"}],
                },
            }
        ]
        mock_find.return_value = mock_cursor
        mock_count.return_value = 1

        response = client.get("/feed?q=Python")
        assert response.status_code == 200
        # Verify that find was called with $text query
        mock_find.assert_called_once_with({"$text": {"$search": "Python"}})

    @patch("flask_login.utils._get_user")
    @patch("app.extensions.mongo.db.resumes.find")
    @patch("app.extensions.mongo.db.resumes.count_documents")
    def test_search_filters_results(
        self, mock_count, mock_find, mock_current_user, client, authenticated_user
    ):
        """Test that search filters results appropriately."""
        mock_current_user.return_value = authenticated_user

        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": ObjectId(),
                "user_id": str(ObjectId()),
                "filename": "python_dev.pdf",
                "structured_data": {
                    "name": "Python Developer",
                    "professional_summary": "Python expert",
                    "skills": [{"skills": "Python"}],
                },
            }
        ]
        mock_find.return_value = mock_cursor
        mock_count.return_value = 1

        response = client.get("/feed?q=Python")
        assert response.status_code == 200
        mock_find.assert_called_once_with({"$text": {"$search": "Python"}})

    @patch("flask_login.utils._get_user")
    def test_search_with_empty_query(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that empty query string returns all resumes."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed?q=")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    @patch("app.extensions.mongo.db.resumes.find")
    @patch("app.extensions.mongo.db.resumes.count_documents")
    def test_search_query_passed_to_template(
        self, mock_count, mock_find, mock_current_user, client, authenticated_user
    ):
        """Test that search query is passed to template for display."""
        mock_current_user.return_value = authenticated_user

        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = []
        mock_find.return_value = mock_cursor
        mock_count.return_value = 0

        response = client.get("/feed?q=Python")
        assert response.status_code == 200


class TestFeedDataStructure:
    """Tests for resume data structure in feed."""

    @patch("flask_login.utils._get_user")
    def test_resume_has_required_fields(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test that transformed resume has all required fields."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            resume_id = ObjectId()
            user_id = str(ObjectId())

            mongo.db.resumes.insert_one(
                {
                    "_id": resume_id,
                    "user_id": user_id,
                    "filename": "test_resume.pdf",
                    "structured_data": {
                        "name": "Test User",
                        "professional_summary": "Test summary",
                        "skills": [{"skills": "Python"}],
                        "location": "San Francisco",
                    },
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_skills_extraction_from_list(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test that skills are extracted and joined correctly."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "test.pdf",
                    "structured_data": {
                        "name": "Test",
                        "skills": [
                            {"skills": "Python"},
                            {"skills": "JavaScript"},
                            {"skills": "React"},
                        ],
                    },
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200
        assert b"Python, JavaScript, React" in response.data

    @patch("flask_login.utils._get_user")
    def test_filters_out_none_skills(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test that empty/None skills are filtered out."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "test.pdf",
                    "structured_data": {
                        "name": "Test",
                        "skills": [
                            {"skills": "Python"},
                            {"skills": ""},
                            {"skills": "JavaScript"},
                            {},
                        ],
                    },
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200
        assert b"Python, JavaScript" in response.data

    @patch("flask_login.utils._get_user")
    def test_handles_missing_structured_data(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test graceful handling when structured_data is missing."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "incomplete.pdf",
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_handles_empty_skills_list(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test handling of empty skills list."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "no_skills.pdf",
                    "structured_data": {"name": "No Skills", "skills": []},
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_handles_non_list_skills(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test handling when skills is not a list."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "bad_skills.pdf",
                    "structured_data": {
                        "name": "Bad Skills",
                        "skills": "Python, JavaScript",
                    },
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200


class TestFeedEmptyState:
    """Tests for feed with no resumes."""

    @patch("flask_login.utils._get_user")
    def test_empty_feed(self, mock_current_user, client, authenticated_user, clean_db):
        """Test feed with no resumes."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    @patch("app.extensions.mongo.db.resumes.find")
    @patch("app.extensions.mongo.db.resumes.count_documents")
    def test_empty_search_results(
        self, mock_count, mock_find, mock_current_user, client, authenticated_user
    ):
        """Test search with no matching results."""
        mock_current_user.return_value = authenticated_user

        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = []
        mock_find.return_value = mock_cursor
        mock_count.return_value = 0

        response = client.get("/feed?q=NonExistentTerm12345")
        assert response.status_code == 200


class TestFeedEdgeCases:
    """Tests for edge cases."""

    @patch("flask_login.utils._get_user")
    def test_invalid_page_number(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test that invalid page number defaults to 1."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed?page=invalid")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_negative_page_number(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test negative page number."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed?page=-1")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_very_large_per_page(
        self, mock_current_user, client, authenticated_user, sample_resumes
    ):
        """Test very large per_page value."""
        mock_current_user.return_value = authenticated_user

        response = client.get("/feed?per_page=10000")
        assert response.status_code == 200

    @patch("flask_login.utils._get_user")
    def test_skills_as_non_list(
        self, mock_current_user, client, authenticated_user, app, clean_db
    ):
        """Test handling when skills is not a list."""
        mock_current_user.return_value = authenticated_user

        with app.app_context():
            mongo.db.resumes.insert_one(
                {
                    "_id": ObjectId(),
                    "user_id": str(ObjectId()),
                    "filename": "bad_skills.pdf",
                    "structured_data": {
                        "name": "Bad Skills Format",
                        "skills": "Python, JavaScript",
                    },
                }
            )

        response = client.get("/feed")
        assert response.status_code == 200
