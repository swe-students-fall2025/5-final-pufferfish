from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.extensions import mongo

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
@login_required
def profile_home():
    """display the user's resume and all comments made on it."""

    # get user resume from db
    resume = mongo.db.resumes.find_one({"user_id": str(current_user.id)})

    if not resume:
        # if no uploads --> render empty state
        return render_template(
            "profile.html",
            user=current_user,
            resume=None,
            comments=[]
        )

    resume_id = str(resume["_id"])

    # get all comments left from other users on this resume
    comments_cursor = mongo.db.comments.find({"resume_id": resume_id}) # TODO: change based on db schema
    comments = []

    for c in comments_cursor:
        comments.append({
            "text": c.get("text", ""),
            "commenter": c.get("commenter", "Anonymous"),
            "_id": str(c.get("_id"))
        })

    # 3. Render profile page with real DB comments
    return render_template(
        "profile.html",
        user=current_user,
        resume=resume,
        comments=comments
    )