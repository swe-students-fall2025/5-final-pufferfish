from app.extensions import mongo

class ResumeService:
    @staticmethod
    def get_highlights(document_id):
        doc = mongo.db.highlights.find_one({"document_id": document_id})
        return doc["highlights"] if doc else {}

    @staticmethod
    def save_highlights(document_id, highlights):
        mongo.db.highlights.update_one(
            {"document_id": document_id},
            {"$set": {"highlights": highlights}},
            upsert=True
        )

