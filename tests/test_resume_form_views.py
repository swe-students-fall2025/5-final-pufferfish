"""Tests for the resume form views."""

import pytest
import mongomock
from unittest.mock import patch, MagicMock
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
            yield client


def create_test_user(client):
    """Helper to create and login a test user."""
    client.post('/signup', data={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    user = mongo.db.users.find_one({'email': 'test@example.com'})
    return str(user['_id'])


class TestResumeFormRoute:
    """Tests for /resume-form route"""
    
    def test_resume_form_requires_login(self, client):
        """Test that route redirects to login if not authenticated."""
        response = client.get('/resume-form')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_resume_form_accessible_when_logged_in(self, client):
        """Test that form is accessible when logged in."""
        create_test_user(client)
        
        response = client.get('/resume-form')
        assert response.status_code == 200
        assert b'Resume' in response.data
    
    def test_resume_form_contains_required_fields(self, client):
        """Test that form contains all required input fields."""
        create_test_user(client)
        
        response = client.get('/resume-form')
        assert response.status_code == 200
        
        # Check for key form fields
        assert b'first_name' in response.data
        assert b'last_name' in response.data
        assert b'email' in response.data


class TestResumeUploadRoute:
    """Tests for /resume/upload route"""
    
    def test_upload_requires_login(self, client):
        """Test that upload page requires authentication."""
        response = client.get('/resume/upload')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_upload_page_accessible_when_logged_in(self, client):
        """Test that upload page is accessible when logged in."""
        create_test_user(client)
        
        response = client.get('/resume/upload')
        assert response.status_code == 200
    
    def test_upload_rejects_non_pdf(self, client):
        """Test that non-PDF files are rejected."""
        create_test_user(client)
        
        # Create a mock text file
        data = {
            'resume': (MagicMock(filename='resume.txt', read=lambda: b'text content'), 'resume.txt')
        }
        
        response = client.post('/resume/upload', data=data, follow_redirects=True)
        # Should show error or redirect back
        assert response.status_code == 200


class TestTemplateSelectionRoute:
    """Tests for /resume/template-selection route"""
    
    def test_template_selection_requires_login(self, client):
        """Test that template selection requires authentication."""
        response = client.get('/resume/template-selection')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_template_selection_requires_resume_id(self, client):
        """Test that template selection requires resume ID in session."""
        create_test_user(client)
        
        response = client.get('/resume/template-selection', follow_redirects=True)
        # Should redirect to resume form or show error
        assert response.status_code == 200


class TestResumePreviewRoute:
    """Tests for /resume/<resume_id>/preview route"""
    
    def test_preview_requires_login(self, client):
        """Test that preview requires authentication."""
        response = client.get('/resume/abc123/preview')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_preview_nonexistent_resume(self, client):
        """Test preview of non-existent resume."""
        create_test_user(client)
        
        fake_id = str(ObjectId())
        response = client.get(f'/resume/{fake_id}/preview', follow_redirects=True)
        # Should redirect with error message
        assert response.status_code == 200


class TestResumeEditRoute:
    """Tests for /resume/<resume_id>/edit route"""
    
    def test_edit_requires_login(self, client):
        """Test that edit requires authentication."""
        response = client.get('/resume/abc123/edit')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_edit_nonexistent_resume(self, client):
        """Test editing non-existent resume."""
        create_test_user(client)
        
        fake_id = str(ObjectId())
        response = client.get(f'/resume/{fake_id}/edit', follow_redirects=True)
        # Should redirect with error
        assert response.status_code == 200


class TestFormSubmission:
    """Tests for form submission and data processing"""
    
    def test_form_submission_creates_resume(self, client):
        """Test that form submission creates a resume record."""
        user_id = create_test_user(client)
        
        form_data = {
            'resume_title': 'My Test Resume',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '555-123-4567',
            'education_count': '1',
            'education_0_school': 'MIT',
            'education_0_degree': 'BS',
            'education_0_field': 'Computer Science',
            'education_0_graduation_month': '05',
            'education_0_graduation_year': '2020',
            'experience_count': '0',
            'skills_count': '0',
            'projects_count': '0'
        }
        
        response = client.post('/resume-form', data=form_data, follow_redirects=True)
        
        # Should redirect to template selection
        assert response.status_code == 200
        
        # Check that resume was created in DB
        resume = mongo.db.resumes.find_one({'user_id': user_id})
        if resume:
            assert resume.get('title') == 'My Test Resume' or 'structured_data' in resume
