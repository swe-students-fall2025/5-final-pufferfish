from app.extensions import mongo, bcrypt
from app.models.user import User
from bson import ObjectId
import datetime


class UserService:
    @staticmethod
    def create_user(email, password, first_name, last_name, headline=""):
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "headline": headline,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }
        result = mongo.db.users.insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    def get_user_by_email(email):
        user_data = mongo.db.users.find_one({"email": email})
        return User.from_mongo(user_data)

    @staticmethod
    def get_user_by_id(user_id):
        try:
            if not user_id:
                return None
            user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            return User.from_mongo(user_data)
        except (ValueError, TypeError, Exception) as e:
            # Invalid ObjectId or other error - return None to prevent crashes
            return None

    @staticmethod
    def verify_password(user, password):
        return bcrypt.check_password_hash(user.password_hash, password)
