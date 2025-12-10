import io
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    jsonify,
    request,
    flash,
    url_for,
    send_file,
)
from flask_login import current_user, login_required
from app.services.resume_service import ResumeService

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/resume/feedback/<resume_id>")
@login_required
def resume_feedback(resume_id):
    """Resume feedback page - view a stored resume and leave comments on it."""
    if not resume_id:
        return jsonify({"error": "resumeId is required"}), 400

    doc, _file = ResumeService.get_resume_pdf(resume_id)
    if not _file:
        return jsonify({"error": "Resume not found"}), 404

    return render_template(
        "resume_feedback.html",
        document_id=resume_id,
        pdf_url=url_for("resume.get_resume_pdf_file", resume_id=resume_id),
        page_title=f"Resume Feedback - {doc.get('filename', 'Resume')}",
    )


@resume_bp.route("/static/pdf/<path:filename>")
def serve_pdf(filename):
    return send_from_directory("../app/static/pdf", filename)


@resume_bp.route("/api/highlights", methods=["GET"])
@login_required
def get_highlights():
    document_id = request.args.get("documentId")
    if not document_id:
        return jsonify({"error": "Missing documentId"}), 400

    # Only show the current user's highlights (each user has their own comments)
    reviewer_id = str(current_user.id)
    highlights = ResumeService.get_highlights(document_id, reviewer_id=reviewer_id)
    return jsonify(highlights), 200


@resume_bp.route("/api/highlights", methods=["POST"])
@login_required
def save_highlights():
    data = request.get_json()
    document_id = data.get("documentId")
    highlights = data.get("highlights")

    if not document_id or highlights is None:
        return jsonify({"error": "Missing required fields"}), 400

    reviewer_id = str(current_user.id)
    reviewer_name = f"{current_user.first_name} {current_user.last_name}"

    ResumeService.save_highlights(document_id, highlights, reviewer_id, reviewer_name)
    return jsonify({"status": "success"}), 200


@resume_bp.route("/resume/<resume_id>/pdf")
def get_resume_pdf_file(resume_id):
    """Stream the stored PDF from MongoDB for viewing/downloading."""
    is_preview = request.args.get("mode") == "preview"
    doc, file_obj = ResumeService.get_resume_pdf(resume_id, is_preview=is_preview)

    if not file_obj:
        return jsonify({"error": "Resume not found"}), 404

    return send_file(
        file_obj,
        mimetype=doc.get("content_type", "application/pdf"),
        download_name=doc.get("filename", "resume.pdf"),
        as_attachment=False,
        conditional=True,
    )
