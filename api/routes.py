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

# OPEN POSITIONS


@api.route("/open_positions/<account_id>", methods=["GET"])
@token_required
def get_open_positions(current_user, account_id):
    """ METHOD THAT GETS ALL OPEN POSITIONS FOR USER
    Args:
        current_user ([dict]): CURRENT USER DATA
        account_id ([int]): CURRENT ACCOUNT ID
    Returns:
        [json]: ALL OPEN POSITION DATA
    """

    try:

        # SPLIT DATA INTO SECTIONS TO ALLOW FOR EASY USE ON FRONT END
        # POSITIONS, OVERALL, TODAY, STRATEGIES

        open_positions = mongo.db.open_positions.find(
            {"Trader": current_user["Name"], "Account_ID": account_id})

        obj = {
            "Positions": [],
            "Overall": {
                "Positions": 0,
                "ROV": 0,
                "Avg_ROV": 0,
                "Profit_Loss": 0
            },
            "Today": {
                "Positions": 0,
                "ROV": 0,
                "Avg_ROV": 0,
                "Profit_Loss": 0
            },
            "Strategies": {}
        }

        i = 0

        overall_avg_rov = []

        today_avg_rov = []

        todays_date = getDatetime().strftime("%Y-%m-%d")

        for position in open_positions:

            if position["Last_Price"] == 0:

                continue

            i += 1

            del position["_id"]

            position["id"] = i

            qty = position["Qty"]

            position["Overall_Change"] = round(
                ((position["Last_Price"] / position["Buy_Price"]) - 1) * 100, 2)

            position["Today_Change"] = round(
                ((position["Last_Price"] / position["Opening_Price"]) - 1) * 100, 2)

            obj["Positions"].append(position)

            obj["Overall"]["Positions"] += 1

            last_price = position["Last_Price"]

            buy_price = position["Buy_Price"]

            opening_price = position["Opening_Price"]

            position_date = datetime.strftime(position["Date"], "%Y-%m-%d")

            if position_date == todays_date:

                obj["Today"]["Positions"] += 1

            obj["Today"]["ROV"] += round(((last_price /
                                           opening_price) - 1) * 100, 2)

            obj["Overall"]["ROV"] += round(
                ((last_price / buy_price) - 1) * 100, 2)

            obj["Today"]["Profit_Loss"] += round(
                ((last_price * qty) - (opening_price * qty)), 2)

            obj["Overall"]["Profit_Loss"] += round(
                ((last_price * qty) - (buy_price * qty)), 2)

            overall_avg_rov.append(
                round(((last_price / buy_price) - 1) * 100, 2))

            today_avg_rov.append(
                round(((last_price / opening_price) - 1) * 100, 2))

            strategy = position["Strategy"]

            if strategy not in obj["Strategies"]:

                obj["Strategies"][strategy] = {
                    "Overall_Change": 0, "Today_Change": 0, "Avg_ROV": [], "Positions": 0}

            obj["Strategies"][strategy]["Overall_Change"] += round(
                ((last_price / buy_price) - 1) * 100, 2)

            obj["Strategies"][strategy]["Today_Change"] += round(
                ((last_price / opening_price) - 1) * 100, 2)

            obj["Strategies"][strategy]["Positions"] += 1

            obj["Strategies"][strategy]["Avg_ROV"].append(round(
                ((last_price / buy_price) - 1) * 100, 2))

            position["Date"] = position["Date"].strftime("%Y-%m-%d %H:%M:%S")

        if len(today_avg_rov) > 0:

            obj["Today"]["Avg_ROV"] = round(statistics.mean(today_avg_rov), 2)

        else:

            obj["Today"]["Avg_ROV"] = 0

        if len(overall_avg_rov) > 0:

            obj["Overall"]["Avg_ROV"] = round(
                statistics.mean(overall_avg_rov), 2)

        else:

            obj["Overall"]["Avg_ROV"] = 0

        obj["Overall"]["ROV"] = round(obj["Overall"]["ROV"], 2)

        obj["Overall"]["Profit_Loss"] = round(obj["Overall"]["Profit_Loss"], 2)

        obj["Today"]["ROV"] = round(obj["Today"]["ROV"], 2)

        obj["Today"]["Profit_Loss"] = round(obj["Today"]["Profit_Loss"], 2)

        for k, v in obj["Strategies"].items():

            if len(v["Avg_ROV"]) > 0:

                v["Avg_ROV"] = round(statistics.mean(v["Avg_ROV"]), 2)

            else:

                v["Avg_ROV"] = 0

        obj["Positions"].reverse()

        return jsonify(obj), 200

    except Exception as e:

        logger.ERROR()

        return jsonify({"error": e}), 500
