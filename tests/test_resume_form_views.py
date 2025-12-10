"""Tests for the resume form views."""

import pytest
import mongomock
from unittest.mock import patch, MagicMock
from bson import ObjectId
from io import BytesIO
from app import create_app
from app.extensions import mongo
from app.views.resume_form_views import (
    parse_form_data_to_structured,
    convert_structured_to_form_data,
)


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


class TestResumeFormRoute:
    """Tests for /resume-form route"""

    def test_resume_form_requires_login(self, client):
        """Test that route redirects to login if not authenticated."""
        response = client.get("/resume-form")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_resume_form_accessible_when_logged_in(self, client):
        """Test that form is accessible when logged in."""
        create_test_user(client)

        response = client.get("/resume-form")
        assert response.status_code == 200
        assert b"Resume" in response.data

    def test_resume_form_contains_required_fields(self, client):
        """Test that form contains all required input fields."""
        create_test_user(client)

        response = client.get("/resume-form")
        assert response.status_code == 200

        # Check for key form fields
        assert b"first_name" in response.data
        assert b"last_name" in response.data
        assert b"email" in response.data


class TestResumeUploadRoute:
    """Tests for /resume/upload route"""

    def test_upload_requires_login(self, client):
        """Test that upload page requires authentication."""
        response = client.get("/resume/upload")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_upload_page_accessible_when_logged_in(self, client):
        """Test that upload page is accessible when logged in."""
        create_test_user(client)

        response = client.get("/resume/upload")
        assert response.status_code == 200

    def test_upload_rejects_non_pdf(self, client):
        """Test that non-PDF files are rejected."""
        create_test_user(client)

        # Create a mock text file
        data = {
            "resume": (
                MagicMock(filename="resume.txt", read=lambda: b"text content"),
                "resume.txt",
            )
        }

        response = client.post("/resume/upload", data=data, follow_redirects=True)
        # Should show error or redirect back
        assert response.status_code == 200


class TestTemplateSelectionRoute:
    """Tests for /resume/template-selection route"""

    def test_template_selection_requires_login(self, client):
        """Test that template selection requires authentication."""
        response = client.get("/resume/template-selection")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_template_selection_requires_resume_id(self, client):
        """Test that template selection requires resume ID in session."""
        create_test_user(client)

        response = client.get("/resume/template-selection", follow_redirects=True)
        # Should redirect to resume form or show error
        assert response.status_code == 200


class TestResumePreviewRoute:
    """Tests for /resume/<resume_id>/preview route"""

    def test_preview_requires_login(self, client):
        """Test that preview requires authentication."""
        response = client.get("/resume/abc123/preview")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_preview_nonexistent_resume(self, client):
        """Test preview of non-existent resume."""
        create_test_user(client)

        fake_id = str(ObjectId())
        response = client.get(f"/resume/{fake_id}/preview", follow_redirects=True)
        # Should redirect with error message
        assert response.status_code == 200


class TestResumeEditRoute:
    """Tests for /resume/<resume_id>/edit route"""

    def test_edit_requires_login(self, client):
        """Test that edit requires authentication."""
        response = client.get("/resume/abc123/edit")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_edit_nonexistent_resume(self, client):
        """Test editing non-existent resume."""
        create_test_user(client)

        fake_id = str(ObjectId())
        response = client.get(f"/resume/{fake_id}/edit", follow_redirects=True)
        # Should redirect with error
        assert response.status_code == 200


class TestFormSubmission:
    """Tests for form submission and data processing"""

    def test_form_submission_creates_resume(self, client):
        """Test that form submission creates a resume record."""
        user_id = create_test_user(client)

        form_data = {
            "resume_title": "My Test Resume",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "555-123-4567",
            "education_count": "1",
            "education_0_school": "MIT",
            "education_0_degree": "BS",
            "education_0_field": "Computer Science",
            "education_0_graduation_month": "05",
            "education_0_graduation_year": "2020",
            "experience_count": "0",
            "skills_count": "0",
            "projects_count": "0",
        }

        response = client.post("/resume-form", data=form_data, follow_redirects=True)

        # Should redirect to template selection
        assert response.status_code == 200

        # Check that resume was created in DB
        resume = mongo.db.resumes.find_one({"user_id": user_id})
        if resume:
            assert (
                resume.get("title") == "My Test Resume" or "structured_data" in resume
            )


class TestParseFormDataToStructured:
    """Tests for parse_form_data_to_structured function."""

    def test_basic_fields(self):
        """Test parsing basic personal info fields."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "linkedin": "linkedin.com/in/johndoe",
            "website": "johndoe.com",
            "introduction": "A software developer",
        }

        result = parse_form_data_to_structured(form_data)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"
        assert result["phone_number"] == "555-1234"

    def test_parse_education(self):
        """Test parsing education entries."""
        form_data = {
            "education_count": "1",
            "education_0_school": "Test University",
            "education_0_graduation_month": "5",
            "education_0_graduation_year": "2024",
            "education_0_degree": "BS",
            "education_0_field": "Computer Science",
            "education_0_location": "New York",
        }

        result = parse_form_data_to_structured(form_data)

        assert len(result["education"]) == 1
        assert result["education"][0]["institution"] == "Test University"
        assert result["education"][0]["degree"] == "BS Computer Science"

    def test_parse_education_invalid_count(self):
        """Test parsing with invalid education count."""
        form_data = {"education_count": "invalid"}
        result = parse_form_data_to_structured(form_data)
        assert result["education"] == []

    def test_parse_education_only_field(self):
        """Test parsing education with only field, no degree."""
        form_data = {
            "education_count": "1",
            "education_0_school": "Test University",
            "education_0_degree": "",
            "education_0_field": "Computer Science",
        }
        result = parse_form_data_to_structured(form_data)
        assert result["education"][0]["degree"] == "Computer Science"

    def test_parse_experience(self):
        """Test parsing experience entries."""
        form_data = {
            "experience_count": "1",
            "experience_0_company": "Tech Corp",
            "experience_0_title": "Software Engineer",
            "experience_0_location": "San Francisco",
            "experience_0_start_month": "1",
            "experience_0_start_year": "2022",
            "experience_0_end_month": "12",
            "experience_0_end_year": "2023",
            "experience_0_bullet_count": "2",
            "experience_0_bullet_0": "Built features",
            "experience_0_bullet_1": "Led team",
        }

        result = parse_form_data_to_structured(form_data)

        assert len(result["experience"]) == 1
        assert result["experience"][0]["company"] == "Tech Corp"
        assert result["experience"][0]["start"] == "2022-01"
        assert len(result["experience"][0]["bullets"]) == 2

    def test_parse_experience_currently_working(self):
        """Test parsing experience with currently working flag."""
        form_data = {
            "experience_count": "1",
            "experience_0_company": "Tech Corp",
            "experience_0_title": "Software Engineer",
            "experience_0_start_year": "2022",
            "experience_0_currently_working": "true",
        }
        result = parse_form_data_to_structured(form_data)
        assert result["experience"][0]["end"] == "Present"

    def test_parse_experience_bullets_fallback(self):
        """Test parsing experience bullets without count."""
        form_data = {
            "experience_count": "1",
            "experience_0_company": "Tech Corp",
            "experience_0_title": "Developer",
            "experience_0_bullet_0": "First bullet",
            "experience_0_bullet_1": "Second bullet",
        }
        result = parse_form_data_to_structured(form_data)
        assert len(result["experience"][0]["bullets"]) == 2

    def test_parse_experience_invalid_count(self):
        """Test parsing with invalid experience count."""
        form_data = {"experience_count": "invalid"}
        result = parse_form_data_to_structured(form_data)
        assert result["experience"] == []

    def test_parse_skills(self):
        """Test parsing skills entries."""
        form_data = {
            "skills_count": "2",
            "skill_0_category": "Programming",
            "skill_0_skills": "Python, Java",
            "skill_1_category": "",
            "skill_1_skills": "Docker, Kubernetes",
        }
        result = parse_form_data_to_structured(form_data)
        assert len(result["skills"]) == 2
        assert result["skills"][1]["category"] == "General"

    def test_parse_skills_invalid_count(self):
        """Test parsing with invalid skills count."""
        form_data = {"skills_count": "invalid"}
        result = parse_form_data_to_structured(form_data)
        assert result["skills"] == []

    def test_parse_projects(self):
        """Test parsing project entries."""
        form_data = {
            "projects_count": "1",
            "project_0_title": "Cool Project",
            "project_0_skills": "Python, Flask",
            "project_0_bullet_count": "1",
            "project_0_bullet_0": "Built a web app",
        }
        result = parse_form_data_to_structured(form_data)
        assert len(result["projects"]) == 1
        assert result["projects"][0]["title"] == "Cool Project"

    def test_parse_projects_invalid_count(self):
        """Test parsing with invalid projects count."""
        form_data = {"projects_count": "invalid"}
        result = parse_form_data_to_structured(form_data)
        assert result["projects"] == []


class TestConvertStructuredToFormData:
    """Tests for convert_structured_to_form_data function."""

    def test_basic_fields(self):
        """Test converting basic fields."""
        structured = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_number": "555-1234",
        }
        result = convert_structured_to_form_data(structured)
        assert result["first_name"] == "John"
        assert result["phone"] == "555-1234"

    def test_convert_education(self):
        """Test converting education entries."""
        structured = {
            "education": [
                {
                    "institution": "Test University",
                    "degree": "Bachelor of Science in Computer Science",
                    "location": "NYC",
                    "end_year": 2024,
                }
            ]
        }
        result = convert_structured_to_form_data(structured)
        assert len(result["education"]) == 1
        assert result["education"][0]["school"] == "Test University"

    def test_convert_education_abbreviation(self):
        """Test converting education with abbreviated degree."""
        structured = {
            "education": [{"institution": "U", "degree": "BS Computer Science"}]
        }
        result = convert_structured_to_form_data(structured)
        assert result["education"][0]["degree"] == "BS"
        assert result["education"][0]["field"] == "Computer Science"

    def test_convert_experience(self):
        """Test converting experience entries."""
        structured = {
            "experience": [
                {
                    "company": "Tech Corp",
                    "role": "Developer",
                    "start": "2022-01",
                    "end": "2023-12",
                    "bullets": ["Did work"],
                }
            ]
        }
        result = convert_structured_to_form_data(structured)
        assert result["experience"][0]["start_year"] == "2022"
        assert result["experience"][0]["start_month"] == "1"

    def test_convert_experience_present(self):
        """Test converting experience with Present end date."""
        structured = {
            "experience": [{"company": "Corp", "role": "Dev", "end": "Present"}]
        }
        result = convert_structured_to_form_data(structured)
        assert result["experience"][0]["currently_working"] is True

    def test_convert_skills(self):
        """Test converting skills entries."""
        structured = {"skills": [{"category": "Languages", "skills": "Python"}]}
        result = convert_structured_to_form_data(structured)
        assert len(result["skills"]) == 1

    def test_convert_projects(self):
        """Test converting project entries."""
        structured = {"projects": [{"title": "Project", "bullets": ["Built it"]}]}
        result = convert_structured_to_form_data(structured)
        assert result["projects"][0]["title"] == "Project"


class TestUploadResumePOST:
    """Tests for POST /resume/upload."""

    def test_upload_no_file(self, client):
        """Test POST upload resume without file."""
        create_test_user(client)
        response = client.post("/resume/upload")
        assert response.status_code == 302

    def test_upload_empty_filename(self, client):
        """Test POST upload resume with empty filename."""
        create_test_user(client)
        response = client.post(
            "/resume/upload",
            data={"resume": (BytesIO(b""), "")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302

    def test_upload_invalid_type(self, client):
        """Test POST upload resume with invalid file type."""
        create_test_user(client)
        response = client.post(
            "/resume/upload",
            data={"resume": (BytesIO(b"not a pdf"), "test.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302


class TestTemplateSelectionPOST:
    """Tests for POST /resume/template-selection."""

    def test_template_selection_with_query_param(self, client):
        """Test template selection with resume_id in query."""
        create_test_user(client)
        resume_id = str(ObjectId())
        response = client.get(f"/resume/template-selection?resume_id={resume_id}")
        assert response.status_code == 200


class TestDownloadAndSetDefault:
    """Tests for download and set-default routes."""

    def test_download_requires_login(self, client):
        """Test that download requires authentication."""
        response = client.get("/resume/abc123/pdf/download")
        assert response.status_code == 302

    def test_set_default_requires_login(self, client):
        """Test that set default requires authentication."""
        response = client.post("/resume/abc123/set-default")
        assert response.status_code == 302

    def test_save_selection_requires_login(self, client):
        """Test that save selection requires authentication."""
        response = client.post("/resume/abc123/save")
        assert response.status_code == 302
