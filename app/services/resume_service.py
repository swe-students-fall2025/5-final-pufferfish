from datetime import datetime
from bson import ObjectId, errors as bson_errors
from gridfs import GridFS
from app.extensions import mongo


class ResumeService:
    @staticmethod
    def get_highlights(document_id):
        doc = mongo.db.highlights.find_one({"document_id": document_id})
        return doc.get("highlights", {}) if doc else {}

    @staticmethod
    def save_highlights(document_id, highlights):
        mongo.db.highlights.update_one(
            {"document_id": document_id},
            {"$set": {"highlights": highlights}},
            upsert=True,
        )

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
