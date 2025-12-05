from flask import Blueprint, render_template, send_from_directory

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/resume')
def resume():
    return render_template('resume.html')

@resume_bp.route('/static/pdf/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('../app/static/pdf', filename)

