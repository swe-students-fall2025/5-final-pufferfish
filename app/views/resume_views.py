from flask import Blueprint, render_template, send_from_directory, jsonify, request
from app.services.resume_service import ResumeService

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/resume/feedback")
def resume_feedback():
    """Resume feedback submission page - allows users to highlight and comment on the resume"""
    document_id = "/static/pdf/jakes-resume.pdf" # TODO: Should be passed in as param
    return render_template(
        "resume_viewer.html",
        document_id=document_id,
        page_title="Submit Resume Feedback",
    )


@resume_bp.route("/static/pdf/<path:filename>")
def serve_pdf(filename):
    return send_from_directory("../app/static/pdf", filename)


@resume_bp.route("/api/highlights", methods=["GET"])
def get_highlights():
    document_id = request.args.get("documentId")
    if not document_id:
        return jsonify({"error": "Missing documentId"}), 400

    highlights = ResumeService.get_highlights(document_id)
    return jsonify(highlights), 200


@resume_bp.route("/api/highlights", methods=["POST"])
def save_highlights():
    data = request.get_json()
    document_id = data.get("documentId")
    highlights = data.get("highlights")

    if not document_id or highlights is None:
        return jsonify({"error": "Missing required fields"}), 400

    ResumeService.save_highlights(document_id, highlights)
    return jsonify({"status": "success"}), 200
