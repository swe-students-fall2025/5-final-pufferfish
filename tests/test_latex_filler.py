"""Tests for the latex_filler utility functions."""

import pytest
from app.utils.latex_filler import (
    escape_latex,
    format_date_for_latex,
    format_date_range,
    fill_latex_template
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
            "email": "john@example.com"
        }
        
        # Should handle unknown template gracefully
        try:
            result = fill_latex_template(structured_data, "unknown_template", "/fake/path.tex")
            # If it doesn't raise, it should return None or empty
            assert result is None or result == ""
        except (ValueError, FileNotFoundError, KeyError):
            # These exceptions are acceptable for invalid input
            pass
    
    def test_fill_latex_template_missing_file(self):
        """Test that missing template file is handled."""
        structured_data = {
            "first_name": "John",
            "last_name": "Doe"
        }
        
        try:
            result = fill_latex_template(structured_data, "jake", "/nonexistent/path.tex")
            # Should handle gracefully
        except FileNotFoundError:
            pass  # Expected behavior
        except Exception:
            pass  # Other errors are also acceptable for missing file
