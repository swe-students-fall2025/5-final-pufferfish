from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.utils.pdf_parser import parse_resume_pdf

resume_form_bp = Blueprint('resume_form', __name__)

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
        
        # Just print it for now (you can see it in terminal)
        print("\n=== FORM DATA RECEIVED ===")
        print(data)
        print("==========================\n")
        
        # TODO: Process and save to database later
        # For now, just redirect to a success page or template selection
        flash('Resume form submitted successfully!')
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

