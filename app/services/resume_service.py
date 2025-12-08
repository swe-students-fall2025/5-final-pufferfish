from datetime import datetime
from bson import ObjectId, errors as bson_errors
from gridfs import GridFS
from app.extensions import mongo


class ResumeService:
    @staticmethod
    def get_highlights(document_id, reviewer_id=None):
        query = {"document_id": document_id}
        if reviewer_id:
            query["reviewer_id"] = reviewer_id
            
        doc = mongo.db.highlights.find_one(query)
        return doc.get("highlights", {}) if doc else {}

    @staticmethod
    def get_all_reviews(document_id):
        # returns a list of all review documents for this resume
        cursor = mongo.db.highlights.find({"document_id": document_id})
        reviews = []
        for doc in cursor:
            reviews.append({
                "reviewer_id": doc.get("reviewer_id"),
                "reviewer_name": doc.get("reviewer_name", "Anonymous"),
                "highlights": doc.get("highlights", {})
            })
        return reviews

    @staticmethod
    def save_highlights(document_id, highlights, reviewer_id=None, reviewer_name="Anonymous"):
        # composite key on document_id AND reviewer_id
        query = {"document_id": document_id}
        if reviewer_id:
            query["reviewer_id"] = reviewer_id
            
        update_data = {
            "highlights": highlights,
            "document_id": document_id
        }
        if reviewer_id:
            update_data["reviewer_id"] = reviewer_id
        if reviewer_name:
            update_data["reviewer_name"] = reviewer_name

        mongo.db.highlights.update_one(
            query,
            {"$set": update_data},
            upsert=True
        )

    @staticmethod
    def get_user_resumes(user_id):
        """Get all resumes owned by a user"""
        cursor = mongo.db.resumes.find({"user_id": user_id})
        resumes = []
        for doc in cursor:
            resumes.append({
                "_id": str(doc.get("_id")),
                "resume_path": doc.get("resume_path"),
                "title": doc.get("title", "Untitled Resume"),
                "created_at": doc.get("created_at")
            })
        return resumes
    
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
                "created_at": doc.get("created_at")
            }
        return None


    @staticmethod
    def save_resume_pdf(file_storage):
        """Store an uploaded PDF in GridFS and a metadata record in MongoDB."""
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
        result = mongo.db.resumes.insert_one(doc)
        return str(result.inserted_id)

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
