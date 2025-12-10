from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
    send_file,
)
from flask_login import current_user
from app.utils.pdf_parser import parse_resume_pdf
from app.utils.latex_filler import fill_latex_template
from app.utils.pdf_generator import compile_latex_to_pdf_bytes
from app.services.resume_service import ResumeService
import os
import io

resume_form_bp = Blueprint("resume_form", __name__)

# Template definitions
TEMPLATES = [
    {
        "id": "jake",
        "name": "Jake Template",
        "description": "A clean and professional template with a traditional layout. Perfect for academic and technical positions.",
        "preview_path": "templates/jake/preview.pdf",
        "preview_image": "templates/jake/preview.png",
        "template_path": "templates/jake/template.tex",
    },
    {
        "id": "harshibar",
        "name": "Harshibar Template",
        "description": "A modern template with a sleek design. Great for creative and tech industry positions.",
        "preview_path": "templates/harshibar/preview.pdf",
        "preview_image": "templates/harshibar/preview.png",
        "template_path": "templates/harshibar/template.tex",
    },
]


def parse_form_data_to_structured(form_data):
    """Parse form data and transform it to the structured JSON schema.

    Args:
        form_data: Dictionary of form data from request.form.to_dict()

    Returns:
        Dictionary matching the structured_data schema
    """
    structured = {
        "first_name": form_data.get("first_name", ""),
        "last_name": form_data.get("last_name", ""),
        "email": form_data.get("email", ""),
        "phone_number": form_data.get("phone", ""),
        "LinkedIn": form_data.get("linkedin", ""),
        "Website": form_data.get("website", ""),
        "professional_summary": form_data.get("introduction", ""),
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
    }

    # Parse Education
    try:
        education_count = int(form_data.get("education_count", 0))
    except (ValueError, TypeError):
        education_count = 0
    for i in range(education_count):
        school = form_data.get(f"education_{i}_school", "").strip()
        if not school:
            continue

        graduation_month = form_data.get(f"education_{i}_graduation_month", "").strip()
        graduation_year = form_data.get(f"education_{i}_graduation_year", "").strip()
        degree = form_data.get(f"education_{i}_degree", "").strip()
        field = form_data.get(f"education_{i}_field", "").strip()
        location = form_data.get(f"education_{i}_location", "").strip()

        # Combine degree and field if both exist
        full_degree = degree
        if field:
            if degree:
                full_degree = f"{degree} {field}"
            else:
                full_degree = field

        edu_entry = {
            "institution": school,
            "degree": full_degree if full_degree else "",
            "location": location,
            "end_month": graduation_month if graduation_month else None,
            "end_year": int(graduation_year) if graduation_year.isdigit() else None,
        }
        structured["education"].append(edu_entry)

    # Parse Experience
    try:
        experience_count = int(form_data.get("experience_count", 0))
    except (ValueError, TypeError):
        experience_count = 0
    for i in range(experience_count):
        company = form_data.get(f"experience_{i}_company", "").strip()
        title = form_data.get(f"experience_{i}_title", "").strip()
        location = form_data.get(f"experience_{i}_location", "").strip()
        if not company or not title:
            continue

        start_month = form_data.get(f"experience_{i}_start_month", "").strip()
        start_year = form_data.get(f"experience_{i}_start_year", "").strip()
        end_month = form_data.get(f"experience_{i}_end_month", "").strip()
        end_year = form_data.get(f"experience_{i}_end_year", "").strip()
        currently_working = form_data.get(f"experience_{i}_currently_working") == "true"

        # Format start date as "YYYY-MM"
        start_date = None
        if start_year and start_year.isdigit():
            if start_month and start_month.isdigit():
                start_date = f"{start_year}-{start_month.zfill(2)}"
            else:
                start_date = f"{start_year}-01"

        # Format end date as "YYYY-MM" or "Present"
        end_date = None
        if currently_working:
            end_date = "Present"
        elif end_year and end_year.isdigit():
            if end_month and end_month.isdigit():
                end_date = f"{end_year}-{end_month.zfill(2)}"
            else:
                end_date = f"{end_year}-12"

        # Parse bullets - try to get count, otherwise iterate until no more bullets
        bullets = []
        bullet_count_str = form_data.get(f"experience_{i}_bullet_count", "")
        if bullet_count_str and bullet_count_str.isdigit():
            bullet_count = int(bullet_count_str)
            for j in range(bullet_count):
                bullet = form_data.get(f"experience_{i}_bullet_{j}", "").strip()
                if bullet:
                    bullets.append(bullet)
        else:
            # Fallback: iterate until we find no more bullets
            j = 0
            while True:
                bullet = form_data.get(f"experience_{i}_bullet_{j}", "").strip()
                if not bullet:
                    break
                bullets.append(bullet)
                j += 1

        exp_entry = {
            "company": company,
            "role": title,
            "location": location,
            "start": start_date,
            "end": end_date,
            "bullets": bullets,
        }
        structured["experience"].append(exp_entry)

    # Parse Skills
    try:
        skills_count = int(form_data.get("skills_count", 0))
    except (ValueError, TypeError):
        skills_count = 0
    for i in range(skills_count):
        category = form_data.get(f"skill_{i}_category", "").strip()
        skills = form_data.get(f"skill_{i}_skills", "").strip()
        if category or skills:
            skill_entry = {
                "category": category if category else "General",
                "skills": skills,
            }
            structured["skills"].append(skill_entry)

    # Parse Projects
    try:
        projects_count = int(form_data.get("projects_count", 0))
    except (ValueError, TypeError):
        projects_count = 0
    for i in range(projects_count):
        title = form_data.get(f"project_{i}_title", "").strip()
        if not title:
            continue

        skills = form_data.get(f"project_{i}_skills", "").strip()

        # Parse bullets - try to get count, otherwise iterate until no more bullets
        bullets = []
        bullet_count_str = form_data.get(f"project_{i}_bullet_count", "")
        if bullet_count_str and bullet_count_str.isdigit():
            bullet_count = int(bullet_count_str)
            for j in range(bullet_count):
                bullet = form_data.get(f"project_{i}_bullet_{j}", "").strip()
                if bullet:
                    bullets.append(bullet)
        else:
            # Fallback: iterate until we find no more bullets
            j = 0
            while True:
                bullet = form_data.get(f"project_{i}_bullet_{j}", "").strip()
                if not bullet:
                    break
                bullets.append(bullet)
                j += 1

        project_entry = {"title": title, "skills": skills, "bullets": bullets}
        structured["projects"].append(project_entry)

    return structured


def convert_structured_to_form_data(structured_data):
    """Convert structured resume data back to form data format for editing.

    Args:
        structured_data: Dictionary matching the structured_data schema

    Returns:
        Dictionary in form data format (prefill_data)
    """
    form_data = {
        "first_name": structured_data.get("first_name", ""),
        "last_name": structured_data.get("last_name", ""),
        "email": structured_data.get("email", ""),
        "phone": structured_data.get("phone_number", ""),
        "linkedin": structured_data.get("LinkedIn", ""),
        "website": structured_data.get("Website", ""),
        "introduction": structured_data.get("professional_summary", ""),
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
    }

    # Convert education
    for edu in structured_data.get("education", []):
        institution = edu.get("institution", "")
        degree_full = edu.get("degree", "")
        location = edu.get("location", "")
        end_month = edu.get("end_month", "")
        end_year = edu.get("end_year", "")

        # Try to split degree into degree and field
        degree = degree_full
        field = ""
        if degree_full:
            # Common patterns: "BS Computer Science", "Bachelor of Arts in Computer Science"
            parts = degree_full.split(" in ", 1)
            if len(parts) == 2:
                degree = parts[0]
                field = parts[1]
            else:
                # Try splitting by space for abbreviations
                parts = degree_full.split(" ", 1)
                if len(parts) == 2 and len(parts[0]) <= 5:  # Likely an abbreviation
                    degree = parts[0]
                    field = parts[1]

        form_data["education"].append(
            {
                "school": institution,
                "location": location,
                "degree": degree,
                "field": field,
                "end_month": end_month if end_month else "",
                "end_year": str(end_year) if end_year else "",
            }
        )

    # Convert experience
    for exp in structured_data.get("experience", []):
        company = exp.get("company", "")
        role = exp.get("role", "")
        location = exp.get("location", "")
        start = exp.get("start", "")
        end = exp.get("end", "Present")
        bullets = exp.get("bullets", [])

        # Parse dates
        start_month = ""
        start_year = ""
        if start and start != "Present":
            if "-" in start:
                parts = start.split("-")
                if len(parts) >= 2:
                    start_year = parts[0]
                    start_month = (
                        parts[1].lstrip("0") if len(parts[1]) > 1 else parts[1]
                    )

        end_month = ""
        end_year = ""
        currently_working = end == "Present"
        if end and end != "Present":
            if "-" in end:
                parts = end.split("-")
                if len(parts) >= 2:
                    end_year = parts[0]
                    end_month = parts[1].lstrip("0") if len(parts[1]) > 1 else parts[1]

        form_data["experience"].append(
            {
                "title": role,
                "company": company,
                "location": location,
                "start_month": start_month,
                "start_year": start_year,
                "end_month": end_month,
                "end_year": end_year,
                "currently_working": currently_working,
                "bullets": bullets,
            }
        )

    # Convert skills
    for skill in structured_data.get("skills", []):
        form_data["skills"].append(
            {"category": skill.get("category", ""), "skills": skill.get("skills", "")}
        )

    # Convert projects
    for proj in structured_data.get("projects", []):
        form_data["projects"].append(
            {
                "title": proj.get("title", ""),
                "name": "",  # Not stored in structured data
                "skills": proj.get("skills", ""),
                "bullets": proj.get("bullets", []),
            }
        )

    return form_data


@resume_form_bp.route("/resume-form", methods=["GET", "POST"])
def resume_form():
    """Resume form page - shows form on GET, processes on POST.
    Requires user to be logged in."""

    # Check if user is logged in
    if not current_user.is_authenticated:
        flash("Please log in to access the resume form.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # Get all form data
        form_data = request.form.to_dict()

        try:
            # Parse form data to structured JSON schema
            structured_data = parse_form_data_to_structured(form_data)

            # Save to MongoDB
            user_id = str(current_user.id) if current_user.is_authenticated else None
            resume_title = form_data.get("resume_title", "").strip()
            if not resume_title:
                resume_title = (
                    f"{structured_data.get('first_name', '')} {structured_data.get('last_name', '')}".strip()
                    or "Untitled Resume"
                )

            current_resume_id = session.get("current_resume_id")
            resume_id = ResumeService.save_resume_structured_data(
                structured_data=structured_data,
                user_id=user_id,
                title=resume_title,
                resume_id=current_resume_id,
            )

            # Store resume_id in session for template selection
            session["current_resume_id"] = resume_id

            # If user uploaded a PDF, set it as the default
            # They can still change to a template on the next page
            uploaded_pdf_file_id = session.get("uploaded_pdf_file_id")
            uploaded_pdf_filename = session.get("uploaded_pdf_filename")

            if uploaded_pdf_file_id:
                from bson import ObjectId
                from app.extensions import mongo

                mongo.db.resumes.update_one(
                    {"_id": ObjectId(resume_id)},
                    {
                        "$set": {
                            "file_id": ObjectId(uploaded_pdf_file_id),
                            "filename": uploaded_pdf_filename,
                            "content_type": "application/pdf",
                            "template_id": "uploaded",
                            "template_name": "Uploaded PDF",
                            "resume_path": f"/resume/{resume_id}/pdf",
                        }
                    },
                )

            flash(
                "Resume saved successfully! Please choose a template or use your uploaded PDF."
            )
            return redirect(url_for("resume_form.select_template"))
        except Exception as e:
            print(f"Error saving resume: {e}")
            import traceback

            traceback.print_exc()
            flash("Error saving resume. Please try again.")
            return redirect(url_for("resume_form.resume_form"))

    # GET request - show the form
    # Clear any existing resume ID so we start fresh, unless specifically prefilled
    # (Edit flow renders template directly, so this route is usually for new resumes)
    session.pop("current_resume_id", None)
    return render_template("resume_form.html")


@resume_form_bp.route("/resume/upload", methods=["GET", "POST"])
def upload_resume():
    """Upload resume page - allows uploading PDF to prefill form and store in MongoDB."""
    if not current_user.is_authenticated:
        flash("Please log in to upload a resume.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if "resume" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["resume"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and file.filename.lower().endswith(".pdf"):
            try:
                from gridfs import GridFS
                from app.extensions import mongo

                # Read the PDF content once
                file.stream.seek(0)
                pdf_content = file.read()

                # Store the PDF in GridFS
                fs = GridFS(mongo.db)
                uploaded_pdf_file_id = fs.put(
                    pdf_content,
                    filename=file.filename,
                    content_type=file.mimetype or "application/pdf",
                )

                # Store the file_id and filename in session for later association with form data
                session["uploaded_pdf_file_id"] = str(uploaded_pdf_file_id)
                session["uploaded_pdf_filename"] = file.filename

                # Parse the PDF for form prefill using a BytesIO stream
                pdf_stream = io.BytesIO(pdf_content)
                extracted_data = parse_resume_pdf(pdf_stream)
                flash(
                    "Resume uploaded and parsed successfully! Please review the prefilled information."
                )

                # Render the form with prefilled data
                return render_template("resume_form.html", prefill_data=extracted_data)
            except Exception as e:
                print(f"Error processing PDF: {e}")
                import traceback

                traceback.print_exc()
                flash(
                    "Error processing PDF. Please try again or fill the form manually."
                )
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload a PDF.")
            return redirect(request.url)

    return render_template("resume_upload.html")


@resume_form_bp.route("/resume/template-selection", methods=["GET", "POST"])
def select_template():
    """Template selection page - shows templates on GET, processes selection on POST."""
    if not current_user.is_authenticated:
        flash("Please log in to select a template.")
        return redirect(url_for("auth.login"))

    # Check if resume_id exists in session (from form submission) or if coming from preview page
    # If coming from preview, we can get resume_id from query param or keep using session
    if "current_resume_id" not in session:
        # Allow access if user has a resume_id in query param (coming from preview page)
        resume_id_from_query = request.args.get("resume_id")
        if resume_id_from_query:
            session["current_resume_id"] = resume_id_from_query
        else:
            flash("Please fill out the resume form first.")
            return redirect(url_for("resume_form.resume_form"))

    if request.method == "POST":
        template_id = request.form.get("template_id")

        # Get resume_id from session
        resume_id = session.get("current_resume_id")
        if not resume_id:
            flash("Resume data not found. Please fill out the form again.")
            return redirect(url_for("resume_form.resume_form"))

        from gridfs import GridFS
        from app.extensions import mongo
        from datetime import datetime
        from bson import ObjectId

        # Check if user chose to use their uploaded PDF
        if template_id == "uploaded_pdf":
            # Use the uploaded PDF from session
            uploaded_pdf_file_id = session.get("uploaded_pdf_file_id")
            uploaded_pdf_filename = session.get("uploaded_pdf_filename")

            if not uploaded_pdf_file_id:
                flash(
                    "No uploaded PDF found. Please upload a resume or select a template."
                )
                return redirect(url_for("resume_form.select_template"))

            try:
                # Update resume document to use the uploaded PDF as the final resume
                mongo.db.resumes.update_one(
                    {"_id": ObjectId(resume_id)},
                    {
                        "$set": {
                            "file_id": ObjectId(uploaded_pdf_file_id),
                            "filename": uploaded_pdf_filename,
                            "content_type": "application/pdf",
                            "template_id": "uploaded",
                            "template_name": "Uploaded PDF",
                            "resume_path": f"/resume/{resume_id}/pdf",
                        }
                    },
                )

                # Clear the uploaded PDF from session since it's now associated
                session.pop("uploaded_pdf_file_id", None)
                session.pop("uploaded_pdf_filename", None)

                flash("Your uploaded resume has been saved successfully!")
                return redirect(
                    url_for("resume_form.preview_resume", resume_id=resume_id)
                )

            except Exception as e:
                print(f"Error saving uploaded PDF: {e}")
                import traceback

                traceback.print_exc()
                flash("Error saving resume. Please try again.")
                return redirect(url_for("resume_form.select_template"))

        # User selected a template - validate it
        template = next((t for t in TEMPLATES if t["id"] == template_id), None)
        if not template:
            flash("Invalid template selected.")
            return redirect(url_for("resume_form.select_template"))

        try:
            # Get structured data from MongoDB
            structured_data = ResumeService.get_resume_structured_data(resume_id)
            if not structured_data:
                flash("Resume data not found in database.")
                return redirect(url_for("resume_form.resume_form"))

            # Get the template path
            template_filename = template["template_path"]
            # Get the static folder path (usually app/static)
            static_folder = os.path.join(current_app.root_path, "static")
            template_path = os.path.join(static_folder, template_filename)

            if not os.path.exists(template_path):
                flash(f"Template file not found: {template_filename}")
                return redirect(url_for("resume_form.select_template"))

            # Fill the LaTeX template with data
            filled_latex = fill_latex_template(
                structured_data, template_id, template_path
            )

            # Log the generated LaTeX for debugging
            print("\n" + "=" * 80)
            print("GENERATED LaTeX CONTENT:")
            print("=" * 80)
            print(filled_latex)
            print("=" * 80 + "\n")

            # Compile LaTeX to PDF
            pdf_bytes, success, error_message = compile_latex_to_pdf_bytes(filled_latex)

            if not success:
                print(f"PDF compilation error: {error_message}")
                flash(f"Error compiling PDF: {error_message[:200]}")
                return redirect(url_for("resume_form.select_template"))

            # Save LaTeX and PDF to GridFS
            from datetime import timezone

            fs = GridFS(mongo.db)

            # Save LaTeX file
            latex_bytes = filled_latex.encode("utf-8")
            latex_file_id = fs.put(
                latex_bytes,
                filename=f"resume_{resume_id}_{template_id}.tex",
                content_type="text/x-latex",
            )

            # Save PDF file
            pdf_file_id = fs.put(
                pdf_bytes,
                filename=f"resume_{resume_id}_{template_id}.pdf",
                content_type="application/pdf",
            )

            # Update resume document with PREVIEW fields
            mongo.db.resumes.update_one(
                {"_id": ObjectId(resume_id)},
                {
                    "$set": {
                        "preview_file_id": pdf_file_id,
                        "preview_latex_file_id": latex_file_id,
                        "preview_template_id": template_id,
                        "preview_template_name": template["name"],
                        "preview_generated_at": datetime.now(timezone.utc),
                    }
                },
            )

            # Clear uploaded PDF from session if user chose a template instead
            session.pop("uploaded_pdf_file_id", None)
            session.pop("uploaded_pdf_filename", None)

            flash(f"Resume generated! Please review and save.")
            return redirect(
                url_for(
                    "resume_form.preview_resume", resume_id=resume_id, mode="preview"
                )
            )

        except Exception as e:
            print(f"Error generating LaTeX: {e}")
            import traceback

            traceback.print_exc()
            flash(f"Error generating resume: {str(e)}")
            return redirect(url_for("resume_form.select_template"))

    # GET request - show template selection page
    # Get resume_id from session or query param
    resume_id = session.get("current_resume_id") or request.args.get("resume_id")

    # Check if user has an uploaded PDF they can use
    has_uploaded_pdf = "uploaded_pdf_file_id" in session
    uploaded_pdf_filename = session.get("uploaded_pdf_filename", "")

    return render_template(
        "resume_template_selection.html",
        templates=TEMPLATES,
        resume_id=resume_id,
        has_uploaded_pdf=has_uploaded_pdf,
        uploaded_pdf_filename=uploaded_pdf_filename,
    )


@resume_form_bp.route("/resume/<resume_id>/edit", methods=["GET"])
def edit_resume(resume_id):
    """Load resume data and redirect to form for editing."""
    if not current_user.is_authenticated:
        flash("Please log in to edit your resume.")
        return redirect(url_for("auth.login"))

    from bson import ObjectId
    from app.extensions import mongo
    from app.services.resume_service import ResumeService

    try:
        # Get structured data from MongoDB
        structured_data = ResumeService.get_resume_structured_data(resume_id)
        if not structured_data:
            flash("Resume data not found.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if user owns this resume
        resume_doc = mongo.db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume_doc or str(resume_doc.get("user_id")) != str(current_user.id):
            flash("You do not have permission to edit this resume.")
            return redirect(url_for("resume_form.resume_form"))

        # Convert structured data back to form format
        prefill_data = convert_structured_to_form_data(structured_data)

        # Explicitly add title from document to prefill data
        prefill_data["resume_title"] = resume_doc.get("title", "")

        # Store resume_id in session so after editing, they can go back to template selection
        session["current_resume_id"] = resume_id

        flash("Resume data loaded. You can now edit your information.")
        return render_template("resume_form.html", prefill_data=prefill_data)

    except Exception as e:
        print(f"Error loading resume for editing: {e}")
        import traceback

        traceback.print_exc()
        flash("Error loading resume data.")
        return redirect(url_for("resume_form.resume_form"))


@resume_form_bp.route("/resume/<resume_id>/preview", methods=["GET"])
def preview_resume(resume_id):
    """Preview page for generated resume."""
    if not current_user.is_authenticated:
        flash("Please log in to view your resume.")
        return redirect(url_for("auth.login"))

    from app.services.resume_service import ResumeService
    from bson import ObjectId
    from gridfs import GridFS
    from app.extensions import mongo

    try:
        # Get resume document
        resume_doc = mongo.db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume_doc:
            flash("Resume not found.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if user owns this resume
        if str(resume_doc.get("user_id")) != str(current_user.id):
            flash("You do not have permission to view this resume.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if PDF exists
        file_id = resume_doc.get("file_id")
        if not file_id:
            flash("PDF not yet generated for this resume.")
            return redirect(url_for("resume_form.resume_form"))

        template_name = resume_doc.get("template_name", "Unknown Template")

        # Check if we are in preview mode
        mode = request.args.get("mode")
        if mode == "preview":
            # In preview mode, we might look for preview_template_name
            template_name = resume_doc.get("preview_template_name", template_name)

        return render_template(
            "resume_preview.html",
            resume_id=resume_id,
            template_name=template_name,
            mode=mode,
        )

    except Exception as e:
        print(f"Error loading resume preview: {e}")
        import traceback

        traceback.print_exc()
        flash("Error loading resume preview.")
        return redirect(url_for("resume_form.resume_form"))


@resume_form_bp.route("/resume/<resume_id>/save", methods=["POST"])
def save_resume_selection(resume_id):
    """Confirm and save the previewed resume as the official one."""
    if not current_user.is_authenticated:
        flash("Please log in to save your resume.")
        return redirect(url_for("auth.login"))

    from bson import ObjectId
    from app.extensions import mongo
    from datetime import datetime, timezone

    try:
        # Get resume document
        resume_doc = mongo.db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume_doc:
            flash("Resume not found.")
            return redirect(url_for("resume_form.resume_form"))

        # Check permission
        if str(resume_doc.get("user_id")) != str(current_user.id):
            flash("You do not have permission to modify this resume.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if we have preview fields
        preview_file_id = resume_doc.get("preview_file_id")
        if not preview_file_id:
            flash("No preview found to save. Please select a template again.")
            return redirect(url_for("resume_form.select_template"))

        # Promote preview fields to official fields
        update_data = {
            "file_id": preview_file_id,
            "template_id": resume_doc.get("preview_template_id", "uploaded"),
            "template_name": resume_doc.get("preview_template_name", "Unknown"),
            "pdf_generated_at": resume_doc.get(
                "preview_generated_at", datetime.now(timezone.utc)
            ),
            "resume_path": f"/resume/{resume_id}/pdf",
        }

        # Optional: update latex_file_id if it exists
        if resume_doc.get("preview_latex_file_id"):
            update_data["latex_file_id"] = resume_doc.get("preview_latex_file_id")
            update_data["latex_generated_at"] = resume_doc.get("preview_generated_at")

        # Clear preview fields
        unset_data = {
            "preview_file_id": "",
            "preview_latex_file_id": "",
            "preview_template_id": "",
            "preview_template_name": "",
            "preview_generated_at": "",
        }

        mongo.db.resumes.update_one(
            {"_id": ObjectId(resume_id)}, {"$set": update_data, "$unset": unset_data}
        )

        flash("Resume saved successfully!")
        return redirect(url_for("resume_form.preview_resume", resume_id=resume_id))

    except Exception as e:
        print(f"Error saving resume selection: {e}")
        import traceback

        traceback.print_exc()
        flash("Error saving resume.")
        return redirect(
            url_for("resume_form.preview_resume", resume_id=resume_id, mode="preview")
        )


@resume_form_bp.route("/resume/<resume_id>/pdf/download", methods=["GET"])
def download_resume_pdf(resume_id):
    """Download the generated PDF resume."""
    if not current_user.is_authenticated:
        flash("Please log in to download your resume.")
        return redirect(url_for("auth.login"))

    from bson import ObjectId
    from gridfs import GridFS
    from app.extensions import mongo

    try:
        # Get resume document
        resume_doc = mongo.db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume_doc:
            flash("Resume not found.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if user owns this resume
        if str(resume_doc.get("user_id")) != str(current_user.id):
            flash("You do not have permission to download this resume.")
            return redirect(url_for("resume_form.resume_form"))

        # Get PDF from GridFS
        file_id = resume_doc.get("file_id")
        if not file_id:
            flash("PDF not yet generated for this resume.")
            return redirect(url_for("resume_form.resume_form"))

        fs = GridFS(mongo.db)
        pdf_file = fs.get(file_id)

        # Get resume title for filename
        resume_title = resume_doc.get("title", "resume")
        # Sanitize filename
        safe_title = "".join(
            c for c in resume_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        filename = f"{safe_title}.pdf" if safe_title else "resume.pdf"

        # Serve PDF for download
        return send_file(
            io.BytesIO(pdf_file.read()),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        print(f"Error downloading PDF: {e}")
        import traceback

        traceback.print_exc()
        flash("Error downloading PDF.")
        return redirect(url_for("resume_form.resume_form"))


@resume_form_bp.route("/resume/<resume_id>/set-default", methods=["POST"])
def set_default_resume(resume_id):
    """Set a resume as the user's default resume."""
    if not current_user.is_authenticated:
        flash("Please log in to set your default resume.")
        return redirect(url_for("auth.login"))

    from app.services.resume_service import ResumeService
    from bson import ObjectId
    from app.extensions import mongo

    try:
        # Get resume document
        resume_doc = mongo.db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume_doc:
            flash("Resume not found.")
            return redirect(url_for("resume_form.resume_form"))

        # Check if user owns this resume
        if str(resume_doc.get("user_id")) != str(current_user.id):
            flash("You do not have permission to set this resume as default.")
            return redirect(url_for("resume_form.resume_form"))

        # Set as current resume
        ResumeService.set_current_resume_for_user(str(current_user.id), resume_id)

        flash("Resume set as default successfully!")
        return redirect(url_for("resume_form.preview_resume", resume_id=resume_id))

    except Exception as e:
        print(f"Error setting default resume: {e}")
        flash("Error setting default resume.")
        return redirect(url_for("resume_form.resume_form"))
