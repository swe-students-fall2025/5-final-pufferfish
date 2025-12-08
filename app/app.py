import datetime
import os

from flask import Flask, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/mydb")
client = MongoClient(mongo_uri)
db = client.get_database()


@app.route("/")
def index():
    print('hello')
    return render_template("index.html")


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
    debug = os.environ.get("debug", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8000, debug=debug)
