from flask import Blueprint, render_template, flash, current_app
from flask_login import login_required, current_user
from app.services.resume_service import ResumeService
from app.extensions import mongo

resume_reviews_bp = Blueprint("resume_reviews", __name__)


@resume_reviews_bp.route("/resume-reviews")
@login_required
def resume_reviews_home():
    """Display the user's resume and all comments made on it."""
    try:
        # Validate database connection
        if not mongo or not hasattr(mongo, "db") or mongo.db is None:
            current_app.logger.error(
                "MongoDB connection not available in resume_reviews_home"
            )
            flash("Database connection error. Please try again later.", "error")
            return render_template(
                "resume_reviews.html",
                user=current_user,
                error="Database connection unavailable.",
                resume_entries=[],
                current_resume_id="",
            )

        # Fetch user's resume entries with error handling
        resume_entries = ResumeService.get_user_resume_entries(current_user.id)

        if not resume_entries:
            return render_template(
                "resume_reviews.html",
                user=current_user,
                error="No resumes found",
                resume_entries=[],
                current_resume_id="",
            )

        # show the earliest (first) resume
        current_resume_id = resume_entries[0]["_id"]

        return render_template(
            "resume_reviews.html",
            user=current_user,
            resume_entries=resume_entries,
            current_resume_id=current_resume_id,
        )

    except Exception as e:
        current_app.logger.error(f"Error loading resume reviews: {str(e)}")
        flash("An error occurred while loading your resumes.", "error")
        return render_template(
            "resume_reviews.html",
            user=current_user,
            error="Unable to load resumes at this time.",
            resume_entries=[],
            current_resume_id="",
        )
