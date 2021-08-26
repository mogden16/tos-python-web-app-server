import json
from typing import Type
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
from api.helpers import maxDrawDown, sharpeRatio

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


def exception_handler(func):

    def wrapper(*args, **kwargs):

        account_id = kwargs["account_id"]

        try:

            return func(*args, **kwargs)

        except KeyError:

            return jsonify({"error": f"Account ID {account_id} Not Found"}), 400

        except TypeError:

            return jsonify({"error": "ERROR"}), 400

        except Exception:

            return jsonify({"error": "ERROR"}), 500

    return wrapper

##########################################################
## GET REQUESTS ##########################################


@exception_handler
@api.route("/account_status/<account_id>", methods=["GET"])
@token_required
def fetch_account_status(current_user, account_id):

    # query the user collection for account status
    status = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
        "Accounts"][account_id]["Active"]

    return jsonify({"account_status": status, "account_id": account_id}), 200


@exception_handler
@api.route("/account_balance/<account_id>", methods=["GET"])
@token_required
def fetch_account_balance(current_user, account_id):

    # query the user collection for account balance
    balance = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
        "Accounts"][account_id]["Account_Balance"]

    return jsonify({"account_balance": balance, "account_id": account_id}), 200


@exception_handler
@api.route("/rate_of_return/<account_id>", methods=["GET"])
@token_required
def fetch_rate_of_return(current_user, account_id):
    # (Current Account Balance - Account Balance from 30 days ago)/(Account balance from 30 days ago) * 12 [if you want yearly RoR]
    # query the user collection for account balance
    balance = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
        "Accounts"][account_id]["Account_Balance"]

    # date 30 days ago
    days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    balance_history = mongo.db.balance_history.find_one(
        {"Account_ID": int(account_id), "Date": days_ago})

    if balance_history != None:

        days_ago_balance = balance_history["Balance"]

        rate_of_return = round(
            (balance - days_ago_balance) / days_ago_balance, 4)

    else:

        rate_of_return = 0

    return jsonify({"rate_of_return": rate_of_return, "account_id": account_id}), 200


@exception_handler
@api.route("/number_of_holdings/<account_id>", methods=["GET"])
@token_required
def fetch_number_of_holdings(current_user, account_id):

    number_of_holdings = mongo.db.open_positions.find(
        {"Account_ID": int(account_id)}).count()

    return jsonify({"number_of_holdings": number_of_holdings, "account_id": account_id}), 200


@exception_handler
@api.route("/account_balance_history/<account_id>", methods=["GET"])
@token_required
def fetch_account_balance_history(current_user, account_id):

    days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    account_balance_history = [history for history in mongo.db.balance_history.find(
        {"Account_ID": int(account_id)}) if history["Date"] >= days_ago]

    for i in account_balance_history:

        del i["_id"]

        del i["Trader"]

        del i["Account_ID"]

    return jsonify({"account_balance_history": account_balance_history, "account_id": account_id}), 200


@exception_handler
@api.route("/profit_loss_history/<account_id>", methods=["GET"])
@token_required
def fetch_profit_loss_history(current_user, account_id):

    days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    profit_loss_history = [history for history in mongo.db.profit_loss_history.find(
        {"Account_ID": int(account_id)}) if history["Date"] >= days_ago]

    for i in profit_loss_history:

        del i["_id"]

        del i["Trader"]

        del i["Account_ID"]

    return jsonify({"profit_loss_history": profit_loss_history, "account_id": account_id}), 200


@exception_handler
@api.route("/queued/<account_id>", methods=["GET"])
@token_required
def fetch_queued(current_user, account_id):

    queued = [queued for queued in mongo.db.queue.find(
        {"Account_ID": int(account_id)})]

    return jsonify({"queued": queued, "account_id": account_id}), 200


@exception_handler
@api.route("/forbidden_symbols/<account_id>", methods=["GET"])
@token_required
def fetch_forbidden_symbols(current_user, account_id):

    forbidden_symbols = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
        "Accounts"][account_id]["forbidden_symbols"]

    return jsonify({"forbidden_symbols": forbidden_symbols, "account_id": account_id}), 200


@exception_handler
@api.route("/best_performing_equities/<account_id>", methods=["GET"])
@token_required
def fetch_best_performing_equities(current_user, account_id):

    symbols = {}

    obj = [{
        "Symbol": "ABC",
        "ROV": 2.3
    },
        {
        "Symbol": "BCA",
        "ROV": 3.2
    },
        {
        "Symbol": "ABC",
        "ROV": -1.1
    },
        {
        "Symbol": "ABC",
        "ROV": 1.7
    },
        {
        "Symbol": "AMC",
        "ROV": 4.4
    },
        {
        "Symbol": "ZWQ",
        "ROV": -3.2
    },
        {
        "Symbol": "ABC",
        "ROV": 1.7
    },
        {
        "Symbol": "AMC",
        "ROV": 1.3
    },
        {
        "Symbol": "QQQ",
        "ROV": -1.3
    },
        {
        "Symbol": "SPY",
        "ROV": 1.9
    },
        {
        "Symbol": "SPY",
        "ROV": -4.2
    }
    ]

    # get top 3 best performing symbols via close_positions
    closed_positions = mongo.db.closed_positions.find(
        {"Account_ID": int(account_id)})

    for position in obj:

        symbol = position["Symbol"]

        if symbol not in symbols:

            symbols[symbol] = 0

        symbols[symbol] += position["ROV"]

    best_performing_equities = [{"Symbol": symbol[0], "ROV": round(symbol[1], 2)} for symbol in sorted(
        symbols.items(), key=lambda t: t[::-1], reverse=True)[0:3]]

    return jsonify({"best_performing_equities": best_performing_equities, "account_id": account_id}), 200


@exception_handler
@api.route("/worst_performing_equities/<account_id>", methods=["GET"])
@token_required
def fetch_worst_performing_equities(current_user, account_id):

    symbols = {}

    obj = [{
        "Symbol": "ABC",
        "ROV": 2.3
    },
        {
        "Symbol": "BCA",
        "ROV": 3.2
    },
        {
        "Symbol": "ABC",
        "ROV": -1.1
    },
        {
        "Symbol": "ABC",
        "ROV": 1.7
    },
        {
        "Symbol": "AMC",
        "ROV": 4.4
    },
        {
        "Symbol": "ZWQ",
        "ROV": -3.2
    },
        {
        "Symbol": "ABC",
        "ROV": 1.7
    },
        {
        "Symbol": "AMC",
        "ROV": 1.3
    },
        {
        "Symbol": "QQQ",
        "ROV": -1.3
    },
        {
        "Symbol": "SPY",
        "ROV": 1.9
    },
        {
        "Symbol": "SPY",
        "ROV": -4.2
    }
    ]

    # get top 3 worse performing symbols via close_positions
    closed_positions = mongo.db.closed_positions.find(
        {"Account_ID": int(account_id)})

    for position in obj:

        symbol = position["Symbol"]

        if symbol not in symbols:

            symbols[symbol] = 0

        symbols[symbol] += position["ROV"]

    worst_performing_equities = [{"Symbol": symbol[0], "ROV": round(symbol[1], 2)} for symbol in sorted(
        symbols.items(), key=lambda t: t[::-1])[0:3]]

    return jsonify({"worst_performing_equities": worst_performing_equities, "account_id": account_id}), 200


@exception_handler
@api.route("/strategies/<account_id>", methods=["GET"])
@token_required
def fetch_strategies(current_user, account_id):

    # STRATEGY, ROV, AVG ROV, WINS, LOSS, FLAT, TOTAL

    closed_positions = mongo.db.closed_positions.find(
        {"Account_ID": int(account_id)})

    strategy_results = mongo.db.users.find_one({"_id": ObjectId(current_user["id"]["$oid"])})[
        "Accounts"][account_id]["Strategies"]

    for v in strategy_results.values():

        if v["Active"]:

            v["Active"] = "Active"

        else:

            v["Active"] = "Inactive"

        v.update({
            "Wins": 0,
            "Loss": 0,
            "Profit_Loss": 0,
            "Avg_ROV": [],
            "Drawdowns": []})

    for position in closed_positions:

        strategy = position["Strategy"]

        if position["ROV"] > 0:

            strategy_results[strategy]["Wins"] += 1

        elif position["ROV"] < 0:

            strategy_results[strategy]["Loss"] += 1

        else:

            continue

        strategy_results[strategy]["Profit_Loss"] += (
            (position["Sell_Price"] * position["Qty"]) - (position["Buy_Price"] * position["Qty"]))

        strategy_results[strategy]["Avg_ROV"].append(position["ROV"])

        strategy_results[strategy]["Drawdowns"].append(
            position["Sell_Price"] - position["Buy_Price"])

    strategies = []

    for key, value in strategy_results.items():

        value["MDD"] = maxDrawDown(value)

        if len(value["Avg_ROV"]) > 1:

            value["Avg_ROV"] = round(statistics.mean(value["Avg_ROV"]), 2)

            value["SR"] = sharpeRatio(value)

        else:

            value["Avg_ROV"] = 0

            value["SR"] = 0

        value["Profit_Loss"] = round(value["Profit_Loss"], 2)

        value["Strategy"] = key

        try:

            value["WRP"] = round(((value["Wins"] - value["Loss"]) /
                                  value["Wins"]) * 100, 2)

        except:

            value["WRP"] = 0

        del strategy_results[key]["Drawdowns"]

        del strategy_results[key]["Wins"]

        del strategy_results[key]["Loss"]

        strategies.append(value)

    return jsonify({"strategies": strategies, "account_id": account_id}), 200


@ exception_handler
@ api.route("/open_positions/<account_id>", methods=["GET"])
@ token_required
def fetch_open_positions(current_user, account_id):

    open_positions = {}

    wow = [
        {
            "Strategy": "TEST1",
            "Symbol": "ABC"
        },
        {
            "Strategy": "TEST1",
            "Symbol": "BCA"
        },
        {
            "Strategy": "TEST1",
            "Symbol": "AMC"
        },
        {
            "Strategy": "TEST1",
            "Symbol": "QQQ"
        },
        {
            "Strategy": "TEST2",
            "Symbol": "ABC"
        },
        {
            "Strategy": "TEST2",
            "Symbol": "SPY"
        }
    ]

    # for position in mongo.db.open_positions.find({"Account_ID": int(account_id)}):
    for position in wow:

        strategy = position["Strategy"]

        if strategy not in open_positions:

            open_positions[strategy] = []

        open_positions[strategy].append(position["Symbol"])

    open_positions = [{"Strategy": k, "Symbols": v}
                      for k, v in open_positions.items()]

    return jsonify({"open_positions": open_positions, "account_id": account_id}), 200

##########################################################
## PUT REQUESTS ##########################################


@exception_handler
@api.route("/change_account_status/<account_id>", methods=["PUT"])
@token_required
def change_account_status(current_user, account_id):

    status = request.json["account_status"]

    if status == "Active":

        status = False

    else:

        status = True

    mongo.db.users.update_one({"_id": ObjectId(current_user["id"]["$oid"])}, {
        "$set": {f"Accounts.{account_id}.Active": status}})

    return jsonify({"account_status": status, "account_id": account_id}), 201


@exception_handler
@api.route("/add_forbidden_symbol/<account_id>", methods=["PUT"])
@token_required
def add_forbidden_symbol(current_user, account_id):

    symbol = request.json["symbol"]

    mongo.db.users.update_one({"_id": ObjectId(current_user["id"]["$oid"])}, {
        "$push": {f"Accounts.{account_id}.forbidden_symbols": symbol.upper()}})

    return jsonify({"account_id": account_id}), 201


@exception_handler
@api.route("/update_strategy/<account_id>", methods=["PUT"])
@token_required
def update_strategy(current_user, account_id):

    data = request.json["data"]

    strategy = data["Strategy"]

    shares = data["Shares"]

    status = data["Status"]

    if status == "Active":

        status = True

    else:

        status = False

    mongo.db.users.update_one({"_id": ObjectId(current_user["id"]["$oid"])}, {
        "$set": {f"Accounts.{account_id}.Strategies.{strategy}": {"Active": status, "Shares": shares}}})

    return jsonify({"account_id": account_id}), 201

##########################################################
## DELETE REQUESTS ##########################################


@exception_handler
@api.route("/remove_forbidden_symbol/<account_id>/<symbol>", methods=["DELETE"])
@token_required
def remove_forbidden_symbol(current_user, account_id, symbol):

    mongo.db.users.update_one({"_id": ObjectId(current_user["id"]["$oid"])}, {
        "$pull": {f"Accounts.{account_id}.forbidden_symbols": symbol.upper()}})

    return jsonify({"account_id": account_id}), 201
