import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def compile_latex_to_pdf(latex_content, output_dir=None):
    """
    Compile LaTeX content to PDF using pdflatex.

    Args:
        latex_content: String containing LaTeX source code
        output_dir: Optional directory to save the PDF. If None, uses a temp directory.

    Returns:
        tuple: (pdf_path, success, error_message)
            - pdf_path: Path to the generated PDF file (or None if failed)
            - success: Boolean indicating if compilation was successful
            - error_message: Error message if compilation failed (or None if successful)
    """
    # Create temporary directory for LaTeX compilation
    temp_dir = tempfile.mkdtemp()

    try:
        # Write LaTeX content to .tex file
        tex_file = os.path.join(temp_dir, "resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # Change to temp directory for compilation (pdflatex needs to be in the same dir)
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Run pdflatex (run twice to resolve references)
            # Use -interaction=nonstopmode to prevent hanging on errors
            # Use -shell-escape if needed for some packages (commented out for security)
            result1 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Run again to resolve references
            result2 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Check if PDF was generated
            pdf_path = os.path.join(temp_dir, "resume.pdf")

            if os.path.exists(pdf_path):
                # If output_dir is specified, copy PDF there
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    final_pdf_path = os.path.join(output_dir, "resume.pdf")
                    shutil.copy2(pdf_path, final_pdf_path)
                    return (final_pdf_path, True, None)
                else:
                    # Return the temp PDF path
                    return (pdf_path, True, None)
            else:
                # Compilation failed - get error from output
                error_output = (
                    "First run stderr:\n"
                    + (result1.stderr or "")
                    + "\n\nFirst run stdout:\n"
                    + (result1.stdout or "")
                )
                if result2.stderr or result2.stdout:
                    error_output += (
                        "\n\nSecond run stderr:\n"
                        + (result2.stderr or "")
                        + "\n\nSecond run stdout:\n"
                        + (result2.stdout or "")
                    )
                # Also check for .log file which might have more details
                log_file = os.path.join(temp_dir, "resume.log")
                if os.path.exists(log_file):
                    try:
                        with open(
                            log_file, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            log_content = f.read()
                            # Get last 50 lines of log for errors
                            log_lines = log_content.split("\n")
                            error_output += "\n\nLast 50 lines of log:\n" + "\n".join(
                                log_lines[-50:]
                            )
                    except:
                        pass
                return (None, False, error_output)

        finally:
            # Restore original directory
            os.chdir(original_dir)

    except subprocess.TimeoutExpired:
        return (None, False, "LaTeX compilation timed out after 30 seconds")
    except Exception as e:
        return (None, False, f"Error during LaTeX compilation: {str(e)}")
    finally:
        # Clean up temp directory (but keep PDF if we're returning it from temp)
        # We'll clean it up after reading the PDF
        pass


def compile_latex_to_pdf_bytes(latex_content):
    """
    Compile LaTeX content to PDF and return as bytes.

    Args:
        latex_content: String containing LaTeX source code

    Returns:
        tuple: (pdf_bytes, success, error_message)
            - pdf_bytes: Bytes of the generated PDF (or None if failed)
            - success: Boolean indicating if compilation was successful
            - error_message: Error message if compilation failed (or None if successful)
    """
    temp_dir = None
    try:
        # Create temporary directory for LaTeX compilation
        temp_dir = tempfile.mkdtemp()

        # Write LaTeX content to .tex file
        tex_file = os.path.join(temp_dir, "resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # Change to temp directory for compilation
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Run pdflatex twice to resolve references
            result1 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            result2 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Check if PDF was generated
            pdf_path = os.path.join(temp_dir, "resume.pdf")

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                return (pdf_bytes, True, None)
            else:
                error_output = result1.stderr + result1.stdout
                if result2.stderr or result2.stdout:
                    error_output += (
                        "\n\nSecond run:\n" + result2.stderr + result2.stdout
                    )
                return (None, False, error_output)

        finally:
            # Restore original directory
            os.chdir(original_dir)

    except subprocess.TimeoutExpired:
        return (None, False, "LaTeX compilation timed out after 30 seconds")
    except Exception as e:
        return (None, False, f"Error during LaTeX compilation: {str(e)}")
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
