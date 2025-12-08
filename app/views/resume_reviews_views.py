from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.resume_service import ResumeService

resume_reviews_bp = Blueprint("resume_reviews", __name__)


@resume_reviews_bp.route("/resume-reviews")
@login_required
def resume_reviews_home():
    """Display the user's resume and all comments made on it."""
    resume_entries = ResumeService.get_user_resume_entries(current_user.id)

    if not resume_entries:
        return render_template(
            "resume_reviews.html",
            user=current_user,
            error="No resumes found",
            resume_entries=[],
            current_resume_id="",
        )

    # Auto-pick the user's current resume if set, otherwise newest (last in list)
    current_resume_id = (
        getattr(current_user, "current_resume_id", None) or resume_entries[-1]["_id"]
    )

    return render_template(
        "resume_reviews.html",
        user=current_user,
        resume_entries=resume_entries,
        current_resume_id=current_resume_id,
    )

