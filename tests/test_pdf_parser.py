
import pytest
from unittest.mock import MagicMock, patch
from app.utils.pdf_parser import parse_resume_pdf

def test_parse_resume_pdf_basic():
    # Mock file stream
    mock_file = MagicMock()
    
    # Mock pypdf.PdfReader
    with patch('app.utils.pdf_parser.PdfReader') as MockReader:
        # Configuration mock reader
        mock_instance = MockReader.return_value
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """
        John Doe
        john.doe@example.com
        (123) 456-7890
        
        Experience
        Software Engineer June 2020 – Present
        Google
        
        Education
        MIT
        BS in CS
        Aug 2016 – May 2020
        
        Skills
        Languages: Python, Java
        
        Projects
        My Cool Project
        """
        mock_instance.pages = [mock_page]
        
        result = parse_resume_pdf(mock_file)
        
        assert result.get('first_name') == 'John'
        assert result.get('last_name') == 'Doe'
        assert result.get('email') == 'john.doe@example.com'
        assert result.get('phone') == '(123) 456-7890'
        
        # Check structured sections
        
        # Experience
        # Expect: [{'title': 'Software Engineer', 'company': 'Google', 'start_year': '2020', 'start_month': '06', ...}]
        assert len(result.get('experience', [])) >= 1
        exp = result['experience'][0]
        assert 'Software Engineer' in exp['title']
        assert 'Google' in exp['company']
        assert exp['start_year'] == '2020'
        
        # Education
        # Expect: [{'school': 'MIT', 'degree': 'BS in CS', ...}]
        assert len(result.get('education', [])) >= 1
        edu = result['education'][0]
        assert 'MIT' in edu['school']
        assert 'CS' in edu.get('degree', '') or 'CS' in edu.get('school', '') # Depending on heuristic
        
        # Skills
        assert len(result.get('skills', [])) >= 1
        skill = result['skills'][0]
        assert 'Languages' in skill['category']
        assert 'Python' in skill['skills']

def test_parse_resume_pdf_no_matches():
    mock_file = MagicMock()
    with patch('app.utils.pdf_parser.PdfReader') as MockReader:
        mock_instance = MockReader.return_value
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Just some random text without headers."
        mock_instance.pages = [mock_page]
        
        result = parse_resume_pdf(mock_file)
        
        # It behaves heuristically for name
        assert result.get('first_name') == 'Just'
        # other fields should be empty lists or None
        assert not result.get('experience')
        assert not result.get('education')
