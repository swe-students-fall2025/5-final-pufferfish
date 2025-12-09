"""Tests for the ResumeService class."""

import pytest
import mongomock
from unittest.mock import patch
from bson import ObjectId
from app import create_app
from app.extensions import mongo
from app.services.resume_service import ResumeService


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    with patch("flask_pymongo.PyMongo.init_app"):
        app = create_app()
        app.config["TESTING"] = True
        mongo.db = mongomock.MongoClient().db

        with app.app_context():
            yield app


@pytest.fixture
def clean_db(app):
    """Clean the database before each test."""
    with app.app_context():
        mongo.db.resumes.delete_many({})
        mongo.db.highlights.delete_many({})
        yield


class TestGetUserResumes:
    """Tests for ResumeService.get_user_resumes()"""

    def test_get_user_resumes_with_multiple_resumes(self, app, clean_db):
        """Test retrieving multiple resumes for a user."""
        with app.app_context():
            user_id = str(ObjectId())

            # insert test resumes
            mongo.db.resumes.insert_many(
                [
                    {
                        "_id": "resume_1",
                        "user_id": user_id,
                        "resume_path": "/static/pdf/resume1.pdf",
                        "title": "Software Engineer Resume",
                        "created_at": "2024-01-15",
                    },
                    {
                        "_id": "resume_2",
                        "user_id": user_id,
                        "resume_path": "/static/pdf/resume2.pdf",
                        "title": "Data Science Resume",
                        "created_at": "2024-02-20",
                    },
                ]
            )

            # get resumes
            resumes = ResumeService.get_user_resumes(user_id)

            assert len(resumes) == 2
            assert resumes[0]["_id"] == "resume_1"
            assert resumes[0]["title"] == "Software Engineer Resume"
            assert resumes[1]["_id"] == "resume_2"
            assert resumes[1]["title"] == "Data Science Resume"

    def test_get_user_resumes_empty_for_new_user(self, app, clean_db):
        """Test that a user with no resumes gets an empty list."""
        with app.app_context():
            user_id = str(ObjectId())
            resumes = ResumeService.get_user_resumes(user_id)

            assert resumes == []

    def test_get_user_resumes_only_returns_user_resumes(self, app, clean_db):
        """Test that only the specified user's resumes are returned."""
        with app.app_context():
            user1_id = str(ObjectId())
            user2_id = str(ObjectId())

            # insert resumes w two different users
            mongo.db.resumes.insert_many(
                [
                    {
                        "_id": "resume_1",
                        "user_id": user1_id,
                        "resume_path": "/static/pdf/resume1.pdf",
                        "title": "User 1 Resume",
                        "created_at": "2024-01-15",
                    },
                    {
                        "_id": "resume_2",
                        "user_id": user2_id,
                        "resume_path": "/static/pdf/resume2.pdf",
                        "title": "User 2 Resume",
                        "created_at": "2024-02-20",
                    },
                ]
            )

            # get resumes for user1
            resumes = ResumeService.get_user_resumes(user1_id)

            assert len(resumes) == 1
            assert resumes[0]["_id"] == "resume_1"
            assert resumes[0]["title"] == "User 1 Resume"


class TestSetCurrentResumeForUser:
    """Tests for ResumeService.set_current_resume_for_user()"""

    def test_sets_pointer_for_existing_user(self, app, clean_db):
        with app.app_context():
            user_id = ObjectId()
            mongo.db.users.insert_one(
                {
                    "_id": user_id,
                    "email": "test@example.com",
                    "password_hash": "hash",
                }
            )

            updated = ResumeService.set_current_resume_for_user(
                str(user_id), "resume_123"
            )

            user = mongo.db.users.find_one({"_id": user_id})
            assert updated is True
            assert user["current_resume_id"] == "resume_123"

    def test_returns_false_when_user_missing(self, app, clean_db):
        with app.app_context():
            updated = ResumeService.set_current_resume_for_user(
                str(ObjectId()), "resume_123"
            )
            assert updated is False


class TestGetResumeById:
    """Tests for ResumeService.get_resume_by_id()"""

    def test_get_resume_by_id_success(self, app, clean_db):
        """Test retrieving a resume by its ID."""
        with app.app_context():
            user_id = str(ObjectId())

            # insert resume
            mongo.db.resumes.insert_one(
                {
                    "_id": "resume_1",
                    "user_id": user_id,
                    "resume_path": "/static/pdf/resume1.pdf",
                    "title": "Test Resume",
                    "created_at": "2024-01-15",
                }
            )

            # get resume
            resume = ResumeService.get_resume_by_id("resume_1")

            assert resume is not None
            assert resume["_id"] == "resume_1"
            assert resume["title"] == "Test Resume"
            assert resume["user_id"] == user_id

    def test_get_resume_by_id_not_found(self, app, clean_db):
        """Test that None is returned for non-existent resume."""
        with app.app_context():
            resume = ResumeService.get_resume_by_id("nonexistent_id")
            assert resume is None


class TestGetAllReviews:
    """Tests for ResumeService.get_all_reviews()"""

    def test_get_all_reviews_with_multiple_reviewers(self, app, clean_db):
        """Test retrieving all reviews for a resume."""
        with app.app_context():
            # insert mock highlights
            mongo.db.highlights.insert_many(
                [
                    {
                        "document_id": "resume_1",
                        "reviewer_id": "reviewer_1",
                        "reviewer_name": "Alice Chen",
                        "highlights": {
                            "1": [
                                {
                                    "id": "hl_1",
                                    "comment": "Great work!",
                                    "text": "Experience",
                                    "rects": [
                                        {"x": 10, "y": 20, "width": 100, "height": 12}
                                    ],
                                }
                            ]
                        },
                    },
                    {
                        "document_id": "resume_1",
                        "reviewer_id": "reviewer_2",
                        "reviewer_name": "Bob Martinez",
                        "highlights": {
                            "1": [
                                {
                                    "id": "hl_2",
                                    "comment": "Good skills",
                                    "text": "Skills",
                                    "rects": [
                                        {"x": 10, "y": 40, "width": 100, "height": 12}
                                    ],
                                }
                            ]
                        },
                    },
                ]
            )

            reviews = ResumeService.get_all_reviews("resume_1")

            assert len(reviews) == 2
            assert reviews[0]["reviewer_name"] == "Alice Chen"
            assert reviews[1]["reviewer_name"] == "Bob Martinez"
            assert "highlights" in reviews[0]
            assert "highlights" in reviews[1]

    def test_get_all_reviews_empty_for_unreviewed_resume(self, app, clean_db):
        """Test that empty list is returned for resume with no reviews."""
        with app.app_context():
            reviews = ResumeService.get_all_reviews("resume_without_reviews")
            assert reviews == []

    def test_get_all_reviews_includes_reviewer_info(self, app, clean_db):
        """Test that reviews include reviewer information."""
        with app.app_context():
            mongo.db.highlights.insert_one(
                {
                    "document_id": "resume_1",
                    "reviewer_id": "reviewer_1",
                    "reviewer_name": "Test Reviewer",
                    "highlights": {},
                }
            )

            reviews = ResumeService.get_all_reviews("resume_1")

            assert len(reviews) == 1
            assert reviews[0]["reviewer_id"] == "reviewer_1"
            assert reviews[0]["reviewer_name"] == "Test Reviewer"


class TestGetHighlights:
    """Tests for ResumeService.get_highlights()"""

    def test_get_highlights_returns_highlights_for_document(self, app, clean_db):
        """Test retrieving highlights for a document."""
        with app.app_context():
            mongo.db.highlights.insert_one(
                {
                    "document_id": "resume_1",
                    "reviewer_id": "reviewer_1",
                    "highlights": {
                        "1": [
                            {
                                "id": "hl_1",
                                "comment": "Great section!",
                                "text": "Experience",
                                "rects": [
                                    {"x": 10, "y": 20, "width": 100, "height": 12}
                                ],
                            }
                        ]
                    },
                }
            )

            highlights = ResumeService.get_highlights("resume_1")

            assert "1" in highlights
            assert len(highlights["1"]) == 1
            assert highlights["1"][0]["comment"] == "Great section!"

    def test_get_highlights_with_reviewer_id(self, app, clean_db):
        """Test retrieving highlights filtered by reviewer_id."""
        with app.app_context():
            # Insert highlights from two different reviewers
            mongo.db.highlights.insert_many(
                [
                    {
                        "document_id": "resume_1",
                        "reviewer_id": "reviewer_1",
                        "highlights": {
                            "1": [{"id": "hl_1", "comment": "From reviewer 1"}]
                        },
                    },
                    {
                        "document_id": "resume_1",
                        "reviewer_id": "reviewer_2",
                        "highlights": {
                            "1": [{"id": "hl_2", "comment": "From reviewer 2"}]
                        },
                    },
                ]
            )

            # Get highlights for specific reviewer
            highlights = ResumeService.get_highlights(
                "resume_1", reviewer_id="reviewer_1"
            )

            assert highlights["1"][0]["comment"] == "From reviewer 1"

    def test_get_highlights_returns_empty_for_nonexistent_document(self, app, clean_db):
        """Test that empty dict is returned for document with no highlights."""
        with app.app_context():
            highlights = ResumeService.get_highlights("nonexistent_resume")
            assert highlights == {}

    def test_get_highlights_returns_empty_for_wrong_reviewer(self, app, clean_db):
        """Test that empty dict is returned when reviewer has no highlights."""
        with app.app_context():
            mongo.db.highlights.insert_one(
                {
                    "document_id": "resume_1",
                    "reviewer_id": "reviewer_1",
                    "highlights": {"1": [{"id": "hl_1", "comment": "Test"}]},
                }
            )

            highlights = ResumeService.get_highlights(
                "resume_1", reviewer_id="other_reviewer"
            )
            assert highlights == {}


class TestSaveHighlights:
    """Tests for ResumeService.save_highlights()"""

    def test_save_highlights_new_document(self, app, clean_db):
        """Test saving highlights for a new document."""
        with app.app_context():
            highlights = {
                "1": [
                    {
                        "id": "hl_1",
                        "comment": "Test comment",
                        "text": "Test text",
                        "rects": [{"x": 10, "y": 20, "width": 100, "height": 12}],
                    }
                ]
            }

            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=highlights,
                reviewer_id="reviewer_1",
                reviewer_name="Test Reviewer",
            )

            # check saved
            saved = mongo.db.highlights.find_one(
                {"document_id": "resume_1", "reviewer_id": "reviewer_1"}
            )

            assert saved is not None
            assert saved["reviewer_name"] == "Test Reviewer"
            assert saved["highlights"]["1"][0]["comment"] == "Test comment"

    def test_save_highlights_update_existing(self, app, clean_db):
        """Test updating highlights for an existing document."""
        with app.app_context():
            # insert initial data
            mongo.db.highlights.insert_one(
                {
                    "document_id": "resume_1",
                    "reviewer_id": "reviewer_1",
                    "reviewer_name": "Old Name",
                    "highlights": {"1": []},
                }
            )

            # update with new highlights
            new_highlights = {
                "1": [
                    {
                        "id": "hl_new",
                        "comment": "Updated comment",
                        "text": "Updated text",
                        "rects": [],
                    }
                ]
            }

            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=new_highlights,
                reviewer_id="reviewer_1",
                reviewer_name="New Name",
            )

            # check updated
            updated = mongo.db.highlights.find_one(
                {"document_id": "resume_1", "reviewer_id": "reviewer_1"}
            )

            assert updated["reviewer_name"] == "New Name"
            assert updated["highlights"]["1"][0]["comment"] == "Updated comment"

    def test_save_highlights_without_reviewer_id(self, app, clean_db):
        """Test saving highlights without a reviewer_id (anonymous)."""
        with app.app_context():
            highlights = {
                "1": [
                    {
                        "id": "hl_1",
                        "comment": "Anonymous comment",
                        "text": "Test",
                        "rects": [],
                    }
                ]
            }

            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=highlights,
                reviewer_id=None,
                reviewer_name="Anonymous",
            )

            saved = mongo.db.highlights.find_one({"document_id": "resume_1"})

            assert saved is not None
            assert saved["reviewer_name"] == "Anonymous"
            assert saved.get("reviewer_id") is None

    def test_save_highlights_multiple_pages(self, app, clean_db):
        """Test saving highlights across multiple pages."""
        with app.app_context():
            highlights = {
                "1": [
                    {
                        "id": "hl_1",
                        "comment": "Page 1 comment",
                        "text": "Text1",
                        "rects": [],
                    }
                ],
                "2": [
                    {
                        "id": "hl_2",
                        "comment": "Page 2 comment",
                        "text": "Text2",
                        "rects": [],
                    }
                ],
                "3": [
                    {
                        "id": "hl_3a",
                        "comment": "Page 3 first",
                        "text": "Text3a",
                        "rects": [],
                    },
                    {
                        "id": "hl_3b",
                        "comment": "Page 3 second",
                        "text": "Text3b",
                        "rects": [],
                    },
                ],
            }

            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=highlights,
                reviewer_id="reviewer_1",
                reviewer_name="Test",
            )

            saved = mongo.db.highlights.find_one({"document_id": "resume_1"})

            assert len(saved["highlights"]) == 3
            assert len(saved["highlights"]["3"]) == 2

    def test_save_highlights_preserves_rect_coordinates(self, app, clean_db):
        """Test that highlight rectangle coordinates are preserved correctly."""
        with app.app_context():
            rects = [
                {"x": 72.5, "y": 150.25, "width": 200.75, "height": 14.5},
                {"x": 72.5, "y": 165.0, "width": 180.0, "height": 14.5},
            ]
            highlights = {
                "1": [
                    {
                        "id": "hl_1",
                        "comment": "Multi-line",
                        "text": "Long text",
                        "rects": rects,
                    }
                ]
            }

            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=highlights,
                reviewer_id="reviewer_1",
            )

            saved = mongo.db.highlights.find_one({"document_id": "resume_1"})
            saved_rects = saved["highlights"]["1"][0]["rects"]

            assert len(saved_rects) == 2
            assert saved_rects[0]["x"] == 72.5
            assert saved_rects[0]["y"] == 150.25
            assert saved_rects[1]["width"] == 180.0


class TestGetResumePdf:
    """Tests for ResumeService.get_resume_pdf()"""

    def test_get_resume_pdf_returns_none_for_invalid_id(self, app, clean_db):
        """Test that invalid resume ID returns None."""
        with app.app_context():
            doc, file_obj = ResumeService.get_resume_pdf("invalid_id")
            assert doc is None
            assert file_obj is None

    def test_get_resume_pdf_returns_none_for_nonexistent(self, app, clean_db):
        """Test that nonexistent resume returns None."""
        with app.app_context():
            doc, file_obj = ResumeService.get_resume_pdf(str(ObjectId()))
            assert doc is None
            assert file_obj is None
