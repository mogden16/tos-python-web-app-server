import json
from flask import Blueprint, current_app, request
from assets.logger import Logger
from flask import jsonify
from flask_cors import cross_origin
import jwt
from functools import wraps
from datetime import datetime, timedelta
import statistics
from pprint import pprint
from bson.objectid import ObjectId
import uuid

from assets.current_datetime import getDatetime
from extensions import mongo

logger = Logger()

api = Blueprint("api", __name__, url_prefix="/api")

logger = Logger()


def token_required(f):
    """ METHOD IS A DECORATOR THATS CHECKS IF TOKEN IS VALID
    Args:
        f ([function]): FUNCTION THAT IS BEING CALLED
    Returns:
        [function]: FUNCTION THAT IS BEING CALLED
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if "x-access-token" in request.headers:

            token = request.headers["x-access-token"]

            try:

                current_user = jwt.decode(
                    token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

            except jwt.ExpiredSignatureError as e:

                logger.WARNING("Token Expired")

                return jsonify({"error": "Token Expired"}), 401

            except jwt.DecodeError as e:

                logger.WARNING("Token Decode Error")

                return jsonify({"error": "Token Decode Error"}), 401

            return f(current_user["user"], *args, **kwargs)

        return jsonify({"error": "Token Does Not Exist"}), 401

    return decorated

##########################################################
## GET REQUESTS ##########################################


@api.route("/account_status/<account_id>", methods=["GET"])
@token_required
def fetch_account_status(current_user, account_id):

    try:

        # query the user collection for account status
        status = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
            "Accounts"][account_id]["Active"]

        return jsonify({"account_status": status, "account_id": account_id}), 200

    except KeyError:

        return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

    except Exception as e:

        return jsonify({"error": "ERROR"}), 500


@api.route("/account_balance/<account_id>", methods=["GET"])
@token_required
def fetch_account_balance(current_user, account_id):

    try:

        # query the user collection for account balance
        balance = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
            "Accounts"][account_id]["Account_Balance"]

        return jsonify({"account_balance": balance, "account_id": account_id}), 200

    except KeyError:

        return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

    except Exception:

        return jsonify({"error": "An Error Occured"}), 500


@api.route("/rate_of_return/<account_id>", methods=["GET"])
@token_required
def fetch_rate_of_return(current_user, account_id):
    # (Current Account Balance - Account Balance from 30 days ago)/(Account balance from 30 days ago) * 12 [if you want yearly RoR]
    try:

        # query the user collection for account balance
        balance = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
            "Accounts"][account_id]["Account_Balance"]

        # date 30 days ago
        days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        days_ago_balance = mongo.db.balance_history.find_one(
            {"Account_ID": int(account_id), "Date": days_ago})["Balance"]

        if days_ago != None:

            rate_of_return = round(
                (balance - days_ago_balance) / days_ago_balance, 4)

        else:

            rate_of_return = 0

        return jsonify({"rate_of_return": rate_of_return, "account_id": account_id}), 200

    except KeyError:

        return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

    except Exception:

        return jsonify({"error": "An Error Occured"}), 500

@api.route("/number_of_holdings/<account_id>", methods=["GET"])
@token_required
def fetch_number_of_holdings(current_user, account_id):
  
    try:

        number_of_holdings = mongo.db.open_positions.find({"Account_ID" : int(account_id)}).count()
        
        return jsonify({"number_of_holdings": number_of_holdings, "account_id": account_id}), 200

    except KeyError:

        return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

    except Exception:

        return jsonify({"error": "An Error Occured"}), 500


##########################################################
## PUT REQUESTS ##########################################

@api.route("/change_account_status/<account_id>", methods=["PUT"])
@token_required
def change_account_status(current_user, account_id):

    try:

        status = request.json["account_status"]

        if status == "Active":

            status = False

        else:

            status = True

        mongo.db.users.update_one({"_id": ObjectId(current_user["id"]["$oid"])}, {
            "$set": {f"Accounts.{account_id}.Active": status}})

        return jsonify({"account_status": status, "account_id": account_id}), 201

    except KeyError:

        return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

    except Exception as e:

        return jsonify({"error": "ERROR"}), 500
