from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.utils.pdf_parser import parse_resume_pdf
from app.services.resume_service import ResumeService

resume_form_bp = Blueprint('resume_form', __name__)


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
        "education": [],
        "experience": [],
        "skills": [],
        "projects": []
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
            "end_month": graduation_month if graduation_month else None,
            "end_year": int(graduation_year) if graduation_year.isdigit() else None
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
            "start": start_date,
            "end": end_date,
            "bullets": bullets
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
                "skills": skills
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
        
        project_entry = {
            "title": title,
            "skills": skills,
            "bullets": bullets
        }
        structured["projects"].append(project_entry)
    
    return structured

@resume_form_bp.route('/resume-form', methods=['GET', 'POST'])
def resume_form():
    """Resume form page - shows form on GET, processes on POST.
    Requires user to be logged in."""
    
    # Check if user is logged in
    if not current_user.is_authenticated:
        flash('Please log in to access the resume form.')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get all form data
        form_data = request.form.to_dict()
        
        try:
            # Parse form data to structured JSON schema
            structured_data = parse_form_data_to_structured(form_data)
            
            # Save to MongoDB
            user_id = str(current_user.id) if current_user.is_authenticated else None
            resume_id = ResumeService.save_resume_structured_data(
                structured_data=structured_data,
                user_id=user_id,
                title=f"{structured_data.get('first_name', '')} {structured_data.get('last_name', '')}".strip() or "Untitled Resume"
            )
            
            flash(f'Resume saved successfully! Resume ID: {resume_id}')
            # TODO: Redirect to template selection page
            return redirect(url_for('resume_form.resume_form'))
        except Exception as e:
            print(f"Error saving resume: {e}")
            flash('Error saving resume. Please try again.')
            return redirect(url_for('resume_form.resume_form'))
    
    # GET request - show the form
    return render_template('resume_form.html')

@resume_form_bp.route('/resume/upload', methods=['GET', 'POST'])
def upload_resume():
    """Upload resume page - allows uploading PDF to prefill form."""
    if not current_user.is_authenticated:
        flash('Please log in to upload a resume.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['resume']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file and file.filename.lower().endswith('.pdf'):
            try:
                # Parse the PDF
                file.stream.seek(0)
                extracted_data = parse_resume_pdf(file.stream)
                flash('Resume parsed successfully! Please review the prefilled information.')
                
                # Render the form with prefilled data
                return render_template('resume_form.html', prefill_data=extracted_data)
            except Exception as e:
                print(f"Error parsing PDF: {e}")
                flash('Error parsing PDF. Please try again or fill the form manually.')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a PDF.')
            return redirect(request.url)
            
    return render_template('resume_upload.html')

