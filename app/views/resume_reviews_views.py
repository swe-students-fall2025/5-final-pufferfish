from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.extensions import mongo

resume_reviews_bp = Blueprint("resume_reviews", __name__)

@resume_reviews_bp.route("/resume-reviews")
@login_required
def resume_reviews_home():
    """Display the user's resume and all comments made on it."""
    
    from flask import request
    from app.services.resume_service import ResumeService
    
    # Get all resumes for the current logged-in user
    user_id = current_user.id
    
    # Get all resumes for this user
    user_resumes = ResumeService.get_user_resumes(user_id)
    
    if not user_resumes:
        return render_template(
            "resume_reviews.html",
            user=current_user,
            error="No resumes found",
            reviews=[],
            user_resumes=[],
            resume_id="",
            resume_path=""
        )
    
    # Prefer a specific resume_id param, otherwise use the user's current pointer, otherwise first
    selected_resume_id = request.args.get("resume_id") or getattr(current_user, "current_resume_id", None)
    current_resume = next(
        (resume for resume in user_resumes if resume.get("_id") == selected_resume_id),
        user_resumes[0],
    )
    resume_id = current_resume["_id"]
    resume_path = current_resume["resume_path"]
    
    # Get all reviews for the current resume
    reviews = ResumeService.get_all_reviews(resume_id)

    return render_template(
        "resume_reviews.html",
        user=current_user,
        resume_id=resume_id,
        resume_path=resume_path,
        reviews=reviews,
        user_resumes=user_resumes,
        current_resume_id=resume_id,
    )