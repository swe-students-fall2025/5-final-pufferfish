from datetime import datetime
from bson import ObjectId, errors as bson_errors
from gridfs import GridFS
from app.extensions import mongo


class ResumeService:
    @staticmethod
    def _parse_datetime(value):
        """Parse ISO strings or datetime objects into datetime; returns None on failure."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Allow trailing Z
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_first_highlight_timestamp(highlights):
        """Find the earliest created_at timestamp across nested highlights."""
        earliest = None
        if not isinstance(highlights, dict):
            return None

        for page_highlights in highlights.values():
            if not isinstance(page_highlights, list):
                continue
            for highlight in page_highlights:
                if not isinstance(highlight, dict):
                    continue
                ts = ResumeService._parse_datetime(highlight.get("created_at"))
                if ts and (earliest is None or ts < earliest):
                    earliest = ts
        return earliest

    @staticmethod
    def get_highlights(document_id, reviewer_id=None):
        query = {"document_id": document_id}
        if reviewer_id:
            query["reviewer_id"] = reviewer_id

        doc = mongo.db.highlights.find_one(query)
        return doc.get("highlights", {}) if doc else {}

    @staticmethod
    def get_all_reviews(document_id):
        # returns a list of all review documents for this resume, sorted by first highlight
        cursor = mongo.db.highlights.find({"document_id": document_id}).sort(
            "first_highlight_created_at", 1
        )
        reviews = []
        for doc in cursor:
            reviews.append(
                {
                    "reviewer_id": doc.get("reviewer_id"),
                    "reviewer_name": doc.get("reviewer_name", "Anonymous"),
                    "highlights": doc.get("highlights", {}),
                }
            )
        return reviews

    @staticmethod
    def save_highlights(
        document_id, highlights, reviewer_id=None, reviewer_name="Anonymous"
    ):
        # composite key on document_id AND reviewer_id
        query = {"document_id": document_id}
        if reviewer_id:
            query["reviewer_id"] = reviewer_id

        # Compute earliest highlight timestamp for sorting
        earliest = ResumeService._extract_first_highlight_timestamp(highlights)

        update_data = {
            "highlights": highlights,
            "document_id": document_id,
            "first_highlight_created_at": earliest,
        }
        if reviewer_id:
            update_data["reviewer_id"] = reviewer_id
        if reviewer_name:
            update_data["reviewer_name"] = reviewer_name

        mongo.db.highlights.update_one(query, {"$set": update_data}, upsert=True)

    @staticmethod
    def get_user_resumes(user_id):
        """Get all resumes owned by a user (oldest first, so newest is on the right)"""
        cursor = mongo.db.resumes.find({"user_id": user_id}).sort("created_at", 1)
        resumes = []
        for doc in cursor:
            resume_id = str(doc.get("_id"))
            resumes.append(
                {
                    "_id": resume_id,
                    # use stored path if present; otherwise fall back to streaming route
                    "resume_path": doc.get("resume_path") or f"/resume/{resume_id}/pdf",
                    "title": doc.get("title", "Untitled Resume"),
                    "created_at": doc.get("created_at"),
                }
            )
        return resumes

    @staticmethod
    def get_user_resume_entries(user_id):
        """Get all resumes for a user with their reviews, ready for the template."""
        user_resumes = ResumeService.get_user_resumes(user_id)
        resume_entries = []
        for resume in user_resumes:
            rid = resume.get("_id")
            created_at = resume.get("created_at")
            created_at_iso = (
                created_at.isoformat()
                if isinstance(created_at, datetime)
                else created_at
            )
            resume_entries.append(
                {
                    "_id": rid,
                    "resume_path": resume.get("resume_path"),
                    "title": resume.get("title"),
                    "created_at": created_at_iso,
                    "reviews": ResumeService.get_all_reviews(rid),
                }
            )
        return resume_entries

    @staticmethod
    def get_resume_by_id(resume_id):
        """Get a specific resume by ID"""
        doc = mongo.db.resumes.find_one({"_id": resume_id})
        if doc:
            return {
                "_id": str(doc.get("_id")),
                "user_id": doc.get("user_id"),
                "resume_path": doc.get("resume_path"),
                "title": doc.get("title", "Untitled Resume"),
                "created_at": doc.get("created_at"),
            }
        return None

    @staticmethod
    def set_current_resume_for_user(user_id, resume_id):
        """
        Persist the pointer to the user's current resume.
        Returns True if we matched a user record.
        """
        if not user_id or not resume_id:
            return False

        try:
            query_id = ObjectId(user_id)
        except (bson_errors.InvalidId, TypeError):
            query_id = user_id

        result = mongo.db.users.update_one(
            {"_id": query_id},
            {"$set": {"current_resume_id": str(resume_id)}},
        )
        return bool(result.matched_count)

    @staticmethod
    def save_resume_pdf(file_storage, user_id=None, title=None):
        """Store an uploaded PDF in GridFS, link it to the user, and record metadata."""
        fs = GridFS(mongo.db)
        file_storage.stream.seek(0)
        file_id = fs.put(
            file_storage.read(),
            filename=file_storage.filename,
            content_type=file_storage.mimetype or "application/pdf",
        )
        doc = {
            "filename": file_storage.filename,
            "content_type": file_storage.mimetype or "application/pdf",
            "file_id": file_id,
            "created_at": datetime.utcnow(),
        }

        if user_id:
            doc["user_id"] = str(user_id)
        if title:
            doc["title"] = title

        result = mongo.db.resumes.insert_one(doc)
        resume_id = str(result.inserted_id)

        if user_id:
            ResumeService.set_current_resume_for_user(user_id, resume_id)

        # persist a convenient streaming path for later lookups
        try:
            mongo.db.resumes.update_one(
                {"_id": ObjectId(resume_id)},
                {"$set": {"resume_path": f"/resume/{resume_id}/pdf"}},
            )
        except (bson_errors.InvalidId, TypeError):
            pass

        return resume_id

    @staticmethod
    def get_resume_pdf(resume_id):
        """Fetch metadata and PDF stream by resumeId."""
        try:
            object_id = ObjectId(resume_id)
        except (bson_errors.InvalidId, TypeError):
            return None, None

        doc = mongo.db.resumes.find_one({"_id": object_id})
        if not doc:
            return None, None

        fs = GridFS(mongo.db)
        file_obj = fs.get(doc["file_id"])
        return doc, file_obj

    @staticmethod
    def save_resume_structured_data(structured_data, user_id=None, title=None):
        """Store structured resume data in MongoDB.
        
        Args:
            structured_data: Dictionary containing structured resume data
            user_id: Optional user ID to associate with the resume
            title: Optional title for the resume
            
        Returns:
            str: The resume_id (MongoDB _id as string)
        """
        doc = {
            "structured_data": structured_data,
            "created_at": datetime.utcnow(),
        }

        if user_id:
            doc["user_id"] = str(user_id)
        if title:
            doc["title"] = title

        result = mongo.db.resumes.insert_one(doc)
        resume_id = str(result.inserted_id)

        if user_id:
            ResumeService.set_current_resume_for_user(user_id, resume_id)

        return resume_id

    @staticmethod
    def get_resume_structured_data(resume_id):
        """Fetch structured resume data by resumeId."""
        try:
            object_id = ObjectId(resume_id)
        except (bson_errors.InvalidId, TypeError):
            return None

        doc = mongo.db.resumes.find_one({"_id": object_id})
        if not doc:
            return None

        return doc.get("structured_data")
