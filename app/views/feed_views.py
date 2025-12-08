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
    query = request.args.get('q', '')
    # skills = request.args.getlist('skills')
    # experience_level = request.args.get('experience_level', '')
    # location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build MongoDB filter
    filters = {}
    
    if query:
        # filters['$or'] = [
        #     {'title': {'$regex': query, '$options': 'i'}},
        #     {'summary': {'$regex': query, '$options': 'i'}},
        #     {'skills': {'$regex': query, '$options': 'i'}}
        # ]

        filters['$text'] = {'$search': query}
    
    # if skills:
    #     filters['skills'] = {'$all': skills}
    
    # if experience_level:
    #     filters['experience_level'] = experience_level
    
    # if location:
    #     filters['location'] = {'$regex': location, '$options': 'i'}

    # Get all resumes from MongoDB
    skip = (page - 1) * per_page
    resumes_cursor = mongo.db.resumes.find(filters).skip(skip).limit(per_page)
    
    resumes = []
    for r in resumes_cursor:
        resumes.append({
            "_id": str(r.get("_id")),
            "user_id": r.get("user_id"),
            "title": r.get("title", ""),
            "summary": r.get("summary", ""),
            "skills": r.get("skills", ""),
            "experience_level": r.get("experience_level", ""),
            "location": r.get("location", ""),
            "filename": r.get("filename", "")
        })
    
    # Get total count for pagination
    total = mongo.db.resumes.count_documents(filters)
    
    return render_template(
        "feed.html",
        resumes=resumes,
        query=query,
        # filters={'skills': skills, 'experience_level': experience_level, 'location': location},
        page=page,
        per_page=per_page,
        total=total
    )