from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.extensions import mongo

resume_reviews_bp = Blueprint("resume_reviews", __name__)

@resume_reviews_bp.route("/resume-reviews")
@login_required
def resume_reviews_home():
    """display the user's resume and all comments made on it."""

    # TODO: using hardcoded resume to match request
    resume_path = "/static/pdf/jakes-resume.pdf"
    
    # get all reviews 
    from app.services.resume_service import ResumeService
    reviews = ResumeService.get_all_reviews(resume_path)

    return render_template(
        "resume_reviews.html",
        user=current_user,
        resume_path=resume_path,
        reviews=reviews 
    )