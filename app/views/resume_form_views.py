from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from app.utils.pdf_parser import parse_resume_pdf

resume_form_bp = Blueprint('resume_form', __name__)

# Template definitions
TEMPLATES = [
    {
        'id': 'jake',
        'name': 'Jake Template',
        'description': 'A clean and professional template with a traditional layout. Perfect for academic and technical positions.',
        'preview_path': 'templates/jake/preview.pdf',
        'template_path': 'templates/jake/template.tex'
    },
    {
        'id': 'harshibar',
        'name': 'Harshibar Template',
        'description': 'A modern template with a sleek design. Great for creative and tech industry positions.',
        'preview_path': 'templates/harshibar/preview.pdf',
        'template_path': 'templates/harshibar/template.tex'
    }
]

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
        data = request.form.to_dict()
        
        # Store form data in session for template selection and PDF generation
        session['resume_form_data'] = data
        
        # Just print it for now (you can see it in terminal)
        print("\n=== FORM DATA RECEIVED ===")
        print(data)
        print("==========================\n")
        
        # Redirect to template selection page
        flash('Resume form submitted successfully! Please choose a template.')
        return redirect(url_for('resume_form.select_template'))
    
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

@resume_form_bp.route('/resume/template-selection', methods=['GET', 'POST'])
def select_template():
    """Template selection page - shows templates on GET, processes selection on POST."""
    if not current_user.is_authenticated:
        flash('Please log in to select a template.')
        return redirect(url_for('auth.login'))
    
    # Check if form data exists in session
    if 'resume_form_data' not in session:
        flash('Please fill out the resume form first.')
        return redirect(url_for('resume_form.resume_form'))
    
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        
        # Validate template ID
        template = next((t for t in TEMPLATES if t['id'] == template_id), None)
        if not template:
            flash('Invalid template selected.')
            return redirect(url_for('resume_form.select_template'))
        
        # Store selected template in session
        session['selected_template'] = template_id
        session['selected_template_path'] = template['template_path']
        
        # TODO: Generate PDF from LaTeX template with form data
        # For now, just show a success message
        flash(f'Template "{template["name"]}" selected! PDF generation coming soon.')
        return redirect(url_for('resume_form.resume_form'))
    
    # GET request - show template selection page
    return render_template('resume_template_selection.html', templates=TEMPLATES)

