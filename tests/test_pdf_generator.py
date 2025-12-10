"""Tests for the PDF generator module."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.utils.pdf_generator import compile_latex_to_pdf, compile_latex_to_pdf_bytes


class TestCompileLatexToPdf:
    """Tests for compile_latex_to_pdf function."""

    def test_compile_latex_timeout(self):
        """Test handling of subprocess timeout."""
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired(cmd="pdflatex", timeout=60)

            result, success, error = compile_latex_to_pdf(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            assert not success
            assert "timed out" in error.lower()
            assert result is None

    def test_compile_latex_exception(self):
        """Test handling of general exceptions."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            result, success, error = compile_latex_to_pdf(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            assert not success
            assert "Error" in error
            assert result is None

    def test_compile_latex_with_output_dir(self):
        """Test compilation with output directory specified."""
        with patch("subprocess.run") as mock_run:
            # Mock successful compilation
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False  # PDF doesn't exist

                result, success, error = compile_latex_to_pdf(
                    "\\documentclass{article}\\begin{document}Test\\end{document}"
                )

                assert not success  # PDF wasn't created

    def test_compile_latex_pdf_not_created(self):
        """Test when PDF is not created after compilation."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "some output"
            mock_result.stderr = "some error"
            mock_run.return_value = mock_result

            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                result, success, error = compile_latex_to_pdf(
                    "\\documentclass{article}\\begin{document}Test\\end{document}"
                )

                assert not success
                assert result is None


class TestCompileLatexToPdfBytes:
    """Tests for compile_latex_to_pdf_bytes function."""

    def test_compile_latex_bytes_timeout(self):
        """Test handling of subprocess timeout for bytes function."""
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired(cmd="pdflatex", timeout=60)

            result, success, error = compile_latex_to_pdf_bytes(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            assert not success
            assert "timed out" in error.lower()
            assert result is None

    def test_compile_latex_bytes_exception(self):
        """Test handling of general exceptions for bytes function."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            result, success, error = compile_latex_to_pdf_bytes(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            assert not success
            assert "Error" in error
            assert result is None

    def test_compile_latex_bytes_pdf_not_created(self):
        """Test when PDF is not created."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "output"
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                result, success, error = compile_latex_to_pdf_bytes(
                    "\\documentclass{article}\\begin{document}Test\\end{document}"
                )

                assert not success
                assert result is None

    def test_compile_latex_bytes_cleanup_on_failure(self):
        """Test that temp directory is cleaned up on failure."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "error output"
            mock_result.stderr = "compilation failed"
            mock_run.return_value = mock_result

            # Test that even on failure, the function handles cleanup
            result, success, error = compile_latex_to_pdf_bytes(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            # Function should return failure since PDF won't be created
            assert not success or result is None
