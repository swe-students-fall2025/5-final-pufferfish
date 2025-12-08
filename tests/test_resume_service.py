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
    with patch('flask_pymongo.PyMongo.init_app'):
        app = create_app()
        app.config['TESTING'] = True
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
            mongo.db.resumes.insert_many([
                {
                    "_id": "resume_1",
                    "user_id": user_id,
                    "resume_path": "/static/pdf/resume1.pdf",
                    "title": "Software Engineer Resume",
                    "created_at": "2024-01-15"
                },
                {
                    "_id": "resume_2",
                    "user_id": user_id,
                    "resume_path": "/static/pdf/resume2.pdf",
                    "title": "Data Science Resume",
                    "created_at": "2024-02-20"
                }
            ])
            
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
            mongo.db.resumes.insert_many([
                {
                    "_id": "resume_1",
                    "user_id": user1_id,
                    "resume_path": "/static/pdf/resume1.pdf",
                    "title": "User 1 Resume",
                    "created_at": "2024-01-15"
                },
                {
                    "_id": "resume_2",
                    "user_id": user2_id,
                    "resume_path": "/static/pdf/resume2.pdf",
                    "title": "User 2 Resume",
                    "created_at": "2024-02-20"
                }
            ])
            
            # get resumes for user1
            resumes = ResumeService.get_user_resumes(user1_id)
            
            assert len(resumes) == 1
            assert resumes[0]["_id"] == "resume_1"
            assert resumes[0]["title"] == "User 1 Resume"


class TestGetResumeById:
    """Tests for ResumeService.get_resume_by_id()"""
    
    def test_get_resume_by_id_success(self, app, clean_db):
        """Test retrieving a resume by its ID."""
        with app.app_context():
            user_id = str(ObjectId())
            
            # insert resume
            mongo.db.resumes.insert_one({
                "_id": "resume_1",
                "user_id": user_id,
                "resume_path": "/static/pdf/resume1.pdf",
                "title": "Test Resume",
                "created_at": "2024-01-15"
            })
            
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
            mongo.db.highlights.insert_many([
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
                                "rects": [{"x": 10, "y": 20, "width": 100, "height": 12}]
                            }
                        ]
                    }
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
                                "rects": [{"x": 10, "y": 40, "width": 100, "height": 12}]
                            }
                        ]
                    }
                }
            ])
            
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
            mongo.db.highlights.insert_one({
                "document_id": "resume_1",
                "reviewer_id": "reviewer_1",
                "reviewer_name": "Test Reviewer",
                "highlights": {}
            })
            
            reviews = ResumeService.get_all_reviews("resume_1")
            
            assert len(reviews) == 1
            assert reviews[0]["reviewer_id"] == "reviewer_1"
            assert reviews[0]["reviewer_name"] == "Test Reviewer"


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
                        "rects": [{"x": 10, "y": 20, "width": 100, "height": 12}]
                    }
                ]
            }
            
            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=highlights,
                reviewer_id="reviewer_1",
                reviewer_name="Test Reviewer"
            )

            # check saved
            saved = mongo.db.highlights.find_one({
                "document_id": "resume_1",
                "reviewer_id": "reviewer_1"
            })
            
            assert saved is not None
            assert saved["reviewer_name"] == "Test Reviewer"
            assert saved["highlights"]["1"][0]["comment"] == "Test comment"
    
    def test_save_highlights_update_existing(self, app, clean_db):
        """Test updating highlights for an existing document."""
        with app.app_context():
            # insert initial data
            mongo.db.highlights.insert_one({
                "document_id": "resume_1",
                "reviewer_id": "reviewer_1",
                "reviewer_name": "Old Name",
                "highlights": {"1": []}
            })
            
            # update with new highlights
            new_highlights = {
                "1": [
                    {
                        "id": "hl_new",
                        "comment": "Updated comment",
                        "text": "Updated text",
                        "rects": []
                    }
                ]
            }
            
            ResumeService.save_highlights(
                document_id="resume_1",
                highlights=new_highlights,
                reviewer_id="reviewer_1",
                reviewer_name="New Name"
            )
            
            # check updated
            updated = mongo.db.highlights.find_one({
                "document_id": "resume_1",
                "reviewer_id": "reviewer_1"
            })
            
            assert updated["reviewer_name"] == "New Name"
            assert updated["highlights"]["1"][0]["comment"] == "Updated comment"
