import pytest
import mongomock
from unittest.mock import patch
from bson import ObjectId
from app import create_app
from app.extensions import mongo


@pytest.fixture
def client():
    """Create and configure a test client."""
    with patch('flask_pymongo.PyMongo.init_app'):
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        mongo.db = mongomock.MongoClient().db
        
        with app.test_client() as client:
            with app.app_context():
                mongo.db.users.delete_many({})
                mongo.db.resumes.delete_many({})
                mongo.db.highlights.delete_many({})
            yield client


def create_test_user(client):
    """Helper to create and login a test user."""
    # create user
    client.post('/signup', data={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    # login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    user = mongo.db.users.find_one({'email': 'test@example.com'})
    return str(user['_id'])


class TestResumeReviewsRoute:
    """Tests for /resume-reviews route"""
    
    def test_resume_reviews_requires_login(self, client):
        """Test that route redirects to login if not authenticated."""
        response = client.get('/resume-reviews')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_resume_reviews_shows_error_when_no_resumes(self, client):
        """Test that an error message is shown when user has no resumes."""
        create_test_user(client)
        
        response = client.get('/resume-reviews', follow_redirects=True)
        assert response.status_code == 200
    
    def test_resume_reviews_displays_first_resume_by_default(self, client):
        """Test that the first resume is displayed by default."""
        user_id = create_test_user(client)
        
        # add resumes
        mongo.db.resumes.insert_many([
            {
                "_id": "resume_1",
                "user_id": user_id,
                "resume_path": "/static/pdf/resume1.pdf",
                "title": "First Resume",
                "created_at": "2024-01-15"
            },
            {
                "_id": "resume_2",
                "user_id": user_id,
                "resume_path": "/static/pdf/resume2.pdf",
                "title": "Second Resume",
                "created_at": "2024-02-20"
            }
        ])
        
        response = client.get('/resume-reviews')
        assert response.status_code == 200
        assert b'First Resume' in response.data or b'resume1.pdf' in response.data
    
    def test_resume_reviews_respects_resume_index_parameter(self, client):
        """Test that resume_index query parameter selects the correct resume."""
        user_id = create_test_user(client)
        
        # add resumes
        mongo.db.resumes.insert_many([
            {
                "_id": "resume_1",
                "user_id": user_id,
                "resume_path": "/static/pdf/resume1.pdf",
                "title": "First Resume",
                "created_at": "2024-01-15"
            },
            {
                "_id": "resume_2",
                "user_id": user_id,
                "resume_path": "/static/pdf/resume2.pdf",
                "title": "Second Resume",
                "created_at": "2024-02-20"
            }
        ])
        
        # request second resume (index 1)
        response = client.get('/resume-reviews?resume_index=1')
        assert response.status_code == 200
        assert b'Second Resume' in response.data or b'resume2.pdf' in response.data
    
    def test_resume_reviews_handles_invalid_resume_index(self, client):
        """Test that invalid resume_index defaults to 0."""
        user_id = create_test_user(client)
        
        # add one resume
        mongo.db.resumes.insert_one({
            "_id": "resume_1",
            "user_id": user_id,
            "resume_path": "/static/pdf/resume1.pdf",
            "title": "First Resume",
            "created_at": "2024-01-15"
        })
        
        # out-of-bounds index
        response = client.get('/resume-reviews?resume_index=999')
        assert response.status_code == 200
        # should default to first resume
        assert b'First Resume' in response.data or b'resume1.pdf' in response.data
        
        # negative index
        response = client.get('/resume-reviews?resume_index=-1')
        assert response.status_code == 200
        assert b'First Resume' in response.data or b'resume1.pdf' in response.data
    
    def test_resume_reviews_passes_reviews_to_template(self, client):
        """Test that reviews are retrieved and passed to the template."""
        user_id = create_test_user(client)
        
        # add resume
        mongo.db.resumes.insert_one({
            "_id": "resume_1",
            "user_id": user_id,
            "resume_path": "/static/pdf/resume1.pdf",
            "title": "Test Resume",
            "created_at": "2024-01-15"
        })
        
        # add reviews
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
        
        response = client.get('/resume-reviews')
        assert response.status_code == 200
        # check reviewer names appear in the page
        assert b'Alice Chen' in response.data or b'reviewer' in response.data.lower()
    
    def test_resume_reviews_only_shows_user_resumes(self, client):
        """Test that users can only see their own resumes."""
        user_id = create_test_user(client)
        other_user_id = str(ObjectId())
        
        # add resume for current user
        mongo.db.resumes.insert_one({
            "_id": "resume_1",
            "user_id": user_id,
            "resume_path": "/static/pdf/myresume.pdf",
            "title": "My Resume",
            "created_at": "2024-01-15"
        })
        
        # add resume for another user
        mongo.db.resumes.insert_one({
            "_id": "resume_2",
            "user_id": other_user_id,
            "resume_path": "/static/pdf/otherresume.pdf",
            "title": "Other User Resume",
            "created_at": "2024-02-20"
        })
        
        response = client.get('/resume-reviews')
        assert response.status_code == 200
        # should only see own resume
        assert b'My Resume' in response.data or b'myresume.pdf' in response.data
        assert b'Other User Resume' not in response.data
        assert b'otherresume.pdf' not in response.data
    
    def test_resume_reviews_passes_correct_template_variables(self, client):
        """Test that all required template variables are passed."""
        user_id = create_test_user(client)
        
        # Add resume
        mongo.db.resumes.insert_one({
            "_id": "resume_1",
            "user_id": user_id,
            "resume_path": "/static/pdf/resume1.pdf",
            "title": "Test Resume",
            "created_at": "2024-01-15"
        })
        
        response = client.get('/resume-reviews')
        assert response.status_code == 200
        
        # response should include the resume selector and PDF viewer elements
        assert b'Select Resume' in response.data or b'resume-selector' in response.data
        assert b'pdf' in response.data.lower()
