from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get("_id"))
        self.email = user_data.get("email")
        self.first_name = user_data.get("first_name")
        self.last_name = user_data.get("last_name")
        self.password_hash = user_data.get("password_hash")
        self.headline = user_data.get("headline")
        self.created_at = user_data.get("created_at")

    def get_id(self):
        return self.id

    @staticmethod
    def from_mongo(data):
        if not data:
            return None
        return User(data)
