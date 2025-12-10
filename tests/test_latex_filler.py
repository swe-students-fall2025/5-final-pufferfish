"""Tests for the latex_filler utility functions."""

import pytest
import os
import tempfile
from app.utils.latex_filler import (
    escape_latex,
    format_date_for_latex,
    format_date_range,
    fill_latex_template,
    fill_jake_template,
    fill_harshibar_template,
)


class TestEscapeLatex:
    """Tests for escape_latex()"""

    def test_escape_latex_special_chars(self):
        """Test escaping LaTeX special characters."""
        # Ampersand
        assert escape_latex("Tom & Jerry") == r"Tom \& Jerry"

        # Percent
        assert escape_latex("100% complete") == r"100\% complete"

        # Dollar sign
        assert escape_latex("$100") == r"\$100"

        # Underscore
        assert escape_latex("file_name") == r"file\_name"

        # Hash
        assert escape_latex("#1 priority") == r"\#1 priority"

    def test_escape_latex_empty_string(self):
        """Test escaping empty string."""
        assert escape_latex("") == ""

    def test_escape_latex_none(self):
        """Test escaping None value."""
        result = escape_latex(None)
        assert result == "" or result is None

    def test_escape_latex_no_special_chars(self):
        """Test string without special characters."""
        text = "Hello World"
        assert escape_latex(text) == text

    def test_escape_latex_multiple_special_chars(self):
        """Test string with multiple special characters."""
        text = "C++ & Java"
        result = escape_latex(text)
        assert r"\&" in result


class TestFormatDateForLatex:
    """Tests for format_date_for_latex()"""

    def test_format_date_present(self):
        """Test formatting 'Present' date."""
        result = format_date_for_latex("Present")
        assert "Present" in result

    def test_format_date_year_month(self):
        """Test formatting YYYY-MM date."""
        result = format_date_for_latex("2023-08")
        # Should contain year and abbreviated month
        assert "2023" in result

    def test_format_date_year_only(self):
        """Test formatting year only."""
        result = format_date_for_latex("2023")
        assert "2023" in result

    def test_format_date_empty(self):
        """Test formatting empty string."""
        result = format_date_for_latex("")
        assert result == "" or result is None or result == "Present"

    def test_format_date_none(self):
        """Test formatting None."""
        result = format_date_for_latex(None)
        assert result == "" or result is None or result == "Present"


class TestFormatDateRange:
    """Tests for format_date_range()"""

    def test_format_date_range_full(self):
        """Test formatting a full date range."""
        result = format_date_range("2020-01", "2023-12")
        assert "2020" in result
        assert "2023" in result

    def test_format_date_range_to_present(self):
        """Test formatting date range to present."""
        result = format_date_range("2020-06", "Present")
        assert "2020" in result
        assert "Present" in result

    def test_format_date_range_empty_end(self):
        """Test formatting date range with empty end date."""
        result = format_date_range("2020-06", None)
        # Should handle gracefully
        assert "2020" in result or result is not None


class TestFillLatexTemplate:
    """Tests for fill_latex_template()"""

    def test_fill_latex_template_invalid_template_id(self):
        """Test that invalid template ID raises appropriate error or returns None."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }

        # Should handle unknown template gracefully
        try:
            result = fill_latex_template(
                structured_data, "unknown_template", "/fake/path.tex"
            )
            # If it doesn't raise, it should return None or empty
            assert result is None or result == ""
        except (ValueError, FileNotFoundError, KeyError):
            # These exceptions are acceptable for invalid input
            pass

    def test_fill_latex_template_missing_file(self):
        """Test that missing template file is handled."""
        structured_data = {"first_name": "John", "last_name": "Doe"}

        try:
            result = fill_latex_template(
                structured_data, "jake", "/nonexistent/path.tex"
            )
            # Should handle gracefully
        except FileNotFoundError:
            pass  # Expected behavior
        except Exception:
            pass  # Other errors are also acceptable for missing file

    def test_fill_latex_template_unknown_id_raises(self):
        """Test that unknown template ID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fill_latex_template({}, "unknown_template", "/path/to/template.tex")
        assert "Unknown template ID" in str(exc_info.value)


class TestEscapeLatexExtended:
    """Extended tests for escape_latex function."""

    def test_escape_backslash(self):
        """Test escaping backslash."""
        result = escape_latex("path\\to\\file")
        assert "textbackslash" in result

    def test_escape_caret(self):
        """Test escaping caret."""
        result = escape_latex("x^2")
        assert "textasciicircum" in result

    def test_escape_tilde(self):
        """Test escaping tilde."""
        result = escape_latex("~home")
        assert "textasciitilde" in result

    def test_escape_non_string(self):
        """Test escaping non-string input."""
        assert escape_latex(123) == "123"

    def test_escape_braces(self):
        """Test escaping braces."""
        assert escape_latex("{braces}") == r"\{braces\}"


class TestFormatDateForLatexExtended:
    """Extended tests for format_date_for_latex function."""

    def test_format_specific_months(self):
        """Test formatting specific months."""
        assert format_date_for_latex("2024-01") == "Jan. 2024"
        assert format_date_for_latex("2024-05") == "May 2024"
        assert format_date_for_latex("2024-06") == "June 2024"
        assert format_date_for_latex("2024-12") == "Dec. 2024"

    def test_format_invalid_month(self):
        """Test formatting with invalid month."""
        assert format_date_for_latex("2024-13") == "2024"
        assert format_date_for_latex("2024-00") == "2024"


class TestFillJakeTemplate:
    """Tests for fill_jake_template function."""

    @pytest.fixture
    def jake_template(self):
        """Create a minimal Jake template for testing."""
        template_content = r"""
\documentclass{article}
\begin{document}
\begin{center}
    \textbf{\Huge \scshape Jake Ryan} \\ \vspace{1pt}
    \small 123-456-7890
\end{center}

%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Test University}{City}
      {BS Computer Science}{2024}
  \resumeSubHeadingListEnd

%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Software Engineer}{Jan 2022 -- Present}
      {Company Name}{City, State}
      \resumeItemListStart
        \resumeItem{Did stuff}
      \resumeItemListEnd
  \resumeSubHeadingListEnd

%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart
      \resumeProjectHeading
          {\textbf{Project Name} $|$ \emph{Python}}{May 2023}
          \resumeItemListStart
            \resumeItem{Built something}
          \resumeItemListEnd
    \resumeSubHeadingListEnd

%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: Python, Java}
    }}
 \end{itemize}

\end{document}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(template_content)
            return f.name

    def test_fill_jake_basic(self, jake_template):
        """Test basic filling of Jake template."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_number": "555-1234",
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "John Doe" in result
        os.unlink(jake_template)

    def test_fill_jake_with_linkedin(self, jake_template):
        """Test Jake template with LinkedIn URL."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "LinkedIn": "johndoe",
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "linkedin.com" in result
        os.unlink(jake_template)

    def test_fill_jake_with_website(self, jake_template):
        """Test Jake template with website."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "Website": "johndoe.com",
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "johndoe.com" in result
        os.unlink(jake_template)

    def test_fill_jake_with_education(self, jake_template):
        """Test Jake template with education."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "education": [
                {
                    "institution": "MIT",
                    "degree": "BS CS",
                    "location": "Cambridge",
                    "end_month": "5",
                    "end_year": 2024,
                }
            ],
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "MIT" in result
        os.unlink(jake_template)

    def test_fill_jake_with_experience(self, jake_template):
        """Test Jake template with experience."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "experience": [
                {
                    "company": "Google",
                    "role": "SWE",
                    "start": "2022-01",
                    "end": "Present",
                    "bullets": ["Built systems"],
                }
            ],
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "Google" in result
        os.unlink(jake_template)

    def test_fill_jake_with_projects(self, jake_template):
        """Test Jake template with projects."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "projects": [
                {"title": "Cool Project", "skills": "Python", "bullets": ["Built it"]}
            ],
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "Cool Project" in result
        os.unlink(jake_template)

    def test_fill_jake_with_skills(self, jake_template):
        """Test Jake template with skills."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe",
            "skills": [{"category": "Languages", "skills": "Python, Java"}],
        }
        result = fill_jake_template(structured_data, jake_template)
        assert "Languages" in result
        os.unlink(jake_template)

    def test_fill_jake_empty_name(self, jake_template):
        """Test Jake template with empty name."""
        structured_data = {"first_name": "", "last_name": ""}
        result = fill_jake_template(structured_data, jake_template)
        assert "Your Name" in result
        os.unlink(jake_template)


class TestFillHarshibarTemplate:
    """Tests for fill_harshibar_template function."""

    @pytest.fixture
    def harshibar_template(self):
        """Create a minimal Harshibar template for testing."""
        template_content = r"""
\documentclass{article}
\begin{document}
\begin{center}
    \textbf{\Huge Name Here} \\ \vspace{5pt}
    \small \faPhone* \texttt{555-5555}
\end{center}

%-----------EXPERIENCE-----------
\section{EXPERIENCE}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Company}{Date}
      {Role}{Location}
  \resumeSubHeadingListEnd

%-----------PROJECTS-----------

\section{PROJECTS}
    \resumeSubHeadingListStart
      \resumeProjectHeading
          {\textbf{Project}} {}
    \resumeSubHeadingListEnd

%-----------EDUCATION-----------
\section {EDUCATION}
  \resumeSubHeadingListStart
    \resumeSubheading
      {University}{Date}
      {Degree}{Location}
  \resumeSubHeadingListEnd

%-----------PROGRAMMING SKILLS-----------
\section{SKILLS}
 \begin{itemize}[leftmargin=0in, label={}]
    \small{\item{
     \textbf{Languages} {: Python}
    }}
 \end{itemize}

\end{document}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(template_content)
            return f.name

    def test_fill_harshibar_basic(self, harshibar_template):
        """Test basic filling of Harshibar template."""
        structured_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "555-9999",
        }
        result = fill_harshibar_template(structured_data, harshibar_template)
        assert "Jane Smith" in result
        os.unlink(harshibar_template)

    def test_fill_harshibar_with_linkedin(self, harshibar_template):
        """Test Harshibar template with LinkedIn."""
        structured_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "LinkedIn": "janesmith",
        }
        result = fill_harshibar_template(structured_data, harshibar_template)
        assert "linkedin.com" in result
        os.unlink(harshibar_template)

    def test_fill_harshibar_with_experience(self, harshibar_template):
        """Test Harshibar template with experience."""
        structured_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "experience": [
                {
                    "company": "Amazon",
                    "role": "SDE",
                    "start": "2021-06",
                    "end": "Present",
                    "bullets": ["Built services"],
                }
            ],
        }
        result = fill_harshibar_template(structured_data, harshibar_template)
        assert "Amazon" in result
        os.unlink(harshibar_template)

    def test_fill_harshibar_with_education(self, harshibar_template):
        """Test Harshibar template with education."""
        structured_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "education": [
                {
                    "institution": "Stanford",
                    "degree": "MS CS",
                    "end_month": "6",
                    "end_year": 2023,
                }
            ],
        }
        result = fill_harshibar_template(structured_data, harshibar_template)
        assert "Stanford" in result
        os.unlink(harshibar_template)

    def test_fill_harshibar_empty_name(self, harshibar_template):
        """Test Harshibar template with empty name."""
        structured_data = {}
        result = fill_harshibar_template(structured_data, harshibar_template)
        assert "Your Name" in result
        os.unlink(harshibar_template)
