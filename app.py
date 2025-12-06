import datetime
import os

from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/mydb")
client = MongoClient(mongo_uri)
db = client.get_database()


@app.route("/")
def index():
    """Landing page."""
    return "Hello, welcome to Puffer Fish!"


@app.route("/resume-form", methods=['GET', 'POST'])
def resume_form():
    """Resume form page - shows form on GET, processes on POST.
    Requires user to be logged in."""
    
    # TODO: Replace this with actual authentication check
    # For now, check if user is logged in via session
    # You can integrate with flask-login or your auth system later
    if 'user_id' not in session:
        # Redirect to login page (you'll need to create this)
        # For now, just allow access - remove this when auth is implemented
        # return redirect(url_for('login'))
        pass
    
    if request.method == 'POST':
        # Get all form data
        data = request.form.to_dict()
        
        # Just print it for now (you can see it in terminal)
        print("\n=== FORM DATA RECEIVED ===")
        print(data)
        print("==========================\n")
        
        # TODO: Process and save to database later
        # For now, just redirect to a success page or template selection
        return redirect(url_for('resume_form'))
    
    # GET request - show the form
    return render_template('resume_form.html')


@app.route("/health")
def health():
    try:
        db.command("ping")

        health_col = db["healthcheck"]
        now = str(datetime.time())

        health_col.update_one(
            {"id": "healthcheck"},
            {"$set": {"last_checked_at": now}},
            upsert=True,
        )

        doc = health_col.find_one({"id": "healthcheck"})
        if not doc:
            raise RuntimeError("healthcheck document missing after write")

        return jsonify({"status": "ok", "DB": str(db.list_collection_names())}), 200

    except PyMongoError as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
