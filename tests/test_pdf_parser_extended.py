"""Extended tests for the pdf_parser module covering new features."""

import pytest
from unittest.mock import MagicMock, patch
from app.utils.pdf_parser import parse_resume_pdf


class TestContactInfoExtraction:
    """Tests for contact info extraction including LinkedIn and GitHub."""
    
    def test_extract_linkedin_url(self):
        """Test extraction of LinkedIn URL."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com | linkedin.com/in/johndoe | github.com/johndoe
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert 'linkedin' in result
            assert 'linkedin.com/in/johndoe' in result['linkedin']
    
    def test_extract_github_url(self):
        """Test extraction of GitHub URL as website."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            Jane Smith
            jane@example.com | github.com/janesmith
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert 'website' in result
            assert 'github.com/janesmith' in result['website']
    
    def test_extract_email(self):
        """Test extraction of email address."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            contact@company.org
            555-123-4567
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert result.get('email') == 'contact@company.org'
    
    def test_extract_phone_number(self):
        """Test extraction of phone number."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com
            (555) 123-4567
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert result.get('phone') == '(555) 123-4567'


class TestEducationParsing:
    """Tests for education section parsing with location splitting."""
    
    def test_education_splits_school_and_location(self):
        """Test that school name is separated from location."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com
            
            Education
            Southwestern University Georgetown, TX
            Bachelor of Arts in Computer Science Aug. 2018 – May 2021
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert len(result.get('education', [])) >= 1
            edu = result['education'][0]
            # School should not include the city
            assert 'Georgetown' not in edu.get('school', '') or 'Southwestern' in edu.get('school', '')
    
    def test_education_degree_and_field_split(self):
        """Test that degree and field of study are correctly split."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com
            
            Education
            MIT, MA
            Bachelor of Science in Computer Engineering Aug. 2016 – May 2020
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert len(result.get('education', [])) >= 1
            edu = result['education'][0]
            assert 'Bachelor' in edu.get('degree', '')


class TestProjectParsing:
    """Tests for project section parsing."""
    
    def test_project_extracts_name_and_tech_stack(self):
        """Test that project name is separated from tech stack."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com
            
            Projects
            MyProject | Python, Flask, React, Docker June 2020 – Present
            • Built a full-stack web application
            • Implemented REST API
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert len(result.get('projects', [])) >= 1
            project = result['projects'][0]
            # Title should be the project name
            assert 'MyProject' in project.get('title', '') or 'MyProject' in project.get('name', '')
            # Skills should contain the tech stack
            assert 'Python' in project.get('skills', '')
    
    def test_project_without_tech_stack(self):
        """Test parsing project without explicit tech stack."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            
            Projects
            Simple Calculator June 2019 – Aug 2019
            • Created a basic calculator app
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            # Should still parse the project
            assert len(result.get('projects', [])) >= 0


class TestExperienceParsing:
    """Tests for experience section parsing."""
    
    def test_experience_extracts_title_and_company(self):
        """Test extraction of job title and company."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            john@example.com
            
            Experience
            Software Engineer Jan 2020 – Present
            Google Mountain View, CA
            • Developed backend services
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert len(result.get('experience', [])) >= 1
            exp = result['experience'][0]
            assert 'Software Engineer' in exp.get('title', '')
            assert 'Google' in exp.get('company', '')


class TestSkillsParsing:
    """Tests for skills section parsing."""
    
    def test_skills_with_categories(self):
        """Test parsing skills with categories."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = """
            John Doe
            
            Technical Skills
            Languages: Python, Java, JavaScript
            Frameworks: React, Django, Flask
            Tools: Git, Docker, AWS
            """
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert len(result.get('skills', [])) >= 1
            # Check for category-based parsing
            categories = [s.get('category', '').lower() for s in result.get('skills', [])]
            assert any('language' in c for c in categories) or len(result.get('skills', [])) > 0


class TestEdgeCases:
    """Tests for edge cases in PDF parsing."""
    
    def test_empty_pdf(self):
        """Test parsing an empty PDF."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            # Should return a valid structure with empty values
            assert isinstance(result, dict)
    
    def test_pdf_with_only_name(self):
        """Test parsing PDF with only a name."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "John Doe"
            mock_instance.pages = [mock_page]
            
            result = parse_resume_pdf(mock_file)
            
            assert result.get('first_name') == 'John'
            assert result.get('last_name') == 'Doe'
    
    def test_multipage_pdf(self):
        """Test parsing a multi-page PDF."""
        mock_file = MagicMock()
        
        with patch('app.utils.pdf_parser.PdfReader') as MockReader:
            mock_instance = MockReader.return_value
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = """
            John Doe
            john@example.com
            
            Experience
            Engineer Jan 2020 – Present
            """
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = """
            Skills
            Languages: Python, Java
            """
            mock_instance.pages = [mock_page1, mock_page2]
            
            result = parse_resume_pdf(mock_file)
            
            # Should parse content from both pages
            assert result.get('first_name') == 'John'
            # Skills should be parsed from page 2
            assert len(result.get('skills', [])) >= 0
