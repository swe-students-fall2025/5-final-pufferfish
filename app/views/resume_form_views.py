from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

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

