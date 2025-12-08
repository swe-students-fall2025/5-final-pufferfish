from flask import Blueprint, render_template, request
from flask_login import login_required
from app.extensions import mongo
from bson import ObjectId

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed")
@login_required
def feed_home():
    """Search and filter through all resumes"""

    # Get query parameters
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Build MongoDB filter
    filters = {}

    if query:
        filters["$text"] = {"$search": query}

    # Get all resumes from MongoDB
    skip = (page - 1) * per_page
    resumes_cursor = mongo.db.resumes.find(filters).skip(skip).limit(per_page)

    resumes = []
    for r in resumes_cursor:
        structured_data = r.get("structured_data", {})

        # Extract skills from all categories
        skills_list = structured_data.get("skills", [])
        all_skills = []
        if isinstance(skills_list, list):
            for skill_obj in skills_list:
                if isinstance(skill_obj, dict):
                    all_skills.append(skill_obj.get("skills", ""))
        skills_str = ", ".join(filter(None, all_skills))

        resumes.append(
            {
                "_id": str(r.get("_id")),
                "user_id": r.get("user_id"),
                "filename": r.get("filename", ""),
                "title": structured_data.get("name", ""),
                "summary": structured_data.get("professional_summary", ""),
                "skills": skills_str,
                "experience_level": "",
                "location": structured_data.get("location", ""),
            }
        )

    # Get total count for pagination
    total = mongo.db.resumes.count_documents(filters)

    return render_template(
        "feed.html",
        resumes=resumes,
        query=query,
        page=page,
        per_page=per_page,
        total=total,
    )
