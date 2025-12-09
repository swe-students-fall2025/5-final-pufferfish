from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_data):
        if not user_data:
            raise ValueError("user_data cannot be None")

        user_id = user_data.get("_id")
        if user_id is None:
            raise ValueError("user_data must have an _id field")

        self.id = str(user_id)
        self.email = user_data.get("email", "")
        self.first_name = user_data.get("first_name", "")
        self.last_name = user_data.get("last_name", "")
        self.password_hash = user_data.get("password_hash", "")
        self.headline = user_data.get("headline", "")
        self.created_at = user_data.get("created_at")
        self.current_resume_id = user_data.get("current_resume_id")

    def get_id(self):
        return self.id

    @staticmethod
    def from_mongo(data):
        if not data:
            return None
        try:
            return User(data)
        except (ValueError, KeyError, AttributeError) as e:
            # Log error in production, but return None to prevent crashes
            return None
