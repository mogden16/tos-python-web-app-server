from flask import Blueprint, current_app, request
from assets.logger import Logger
from flask import jsonify
from flask_cors import cross_origin
import jwt
from datetime import datetime, timedelta
from bson import json_util
import json

from extensions import mongo, bcrypt

logger = Logger()

auth = Blueprint("auth", __name__)


@auth.route("/checkAuthToken")
@cross_origin()
def checkAuthToken():

    token = None

    if "x-access-token" in request.headers:

        token = request.headers["x-access-token"]

        try:

            jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

            return jsonify({"success": True}), 200

        except Exception as e:

            logger.WARNING("Token Expired")

            return jsonify({"error": "Token Expired"}), 401

    logger.WARNING("Missing Token")

    return jsonify({"error": "Missing Token"}), 401


@auth.route("/login", methods=["POST"])
@cross_origin()
def login():

    try:
        
        username = request.json["username"]

        password = request.json["password"]

        user = mongo.db.users.find_one({
            "Username": username
        })

        if user:

            if bcrypt.check_password_hash(user["Password"], password):

                obj = {
                    "id": user["_id"],
                    "Name": user["Name"]
                }

                token = jwt.encode({"user": json.loads(json_util.dumps(obj)), "exp": datetime.utcnow(
                ) + timedelta(hours=24)}, current_app.config["SECRET_KEY"], algorithm="HS256")

                logger.INFO(f"Login Successful - USERNAME:{username}")

                del user["Username"]

                del user["Password"]

                del user["_id"]

                obj = {
                    "Username" : user["Name"], 
                    "Account_IDs" : [account_id for account_id in user["Accounts"].keys()]
                }

                return jsonify({"token": token, "data" : obj})

        logger.WARNING(
            f"Invalid Credentials - USERNAME:{username} PASSWORD:{password}")

        return jsonify({"error": "Invalid Credentials"}), 401

    except Exception as e:
        print(e)

        logger.WARNING(f"Invalid Credentials")

        return jsonify({"error": "Invalid Credentials"}), 401
