from app.extensions import mongo

class ResumeService:
    @staticmethod
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

