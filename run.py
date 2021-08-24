from flask import Flask
from datetime import datetime, timedelta
from flask_cors import CORS
from dotenv import load_dotenv
import os

from auth.routes import auth
from api.routes import api
from extensions import mongo, bcrypt

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=f"{THIS_FOLDER}/assets/.env")

MONGO_URI = os.getenv('MONGO_URI')


def create_app():

    app = Flask(__name__)

    CORS(app)

    app.config["MONGO_URI"] = MONGO_URI

    mongo.init_app(app)

    bcrypt.init_app(app)

    app.config["SECRET_KEY"] = (mongo.db.users.find_one(
        {"Name": "Trey Thomas"}))["Password"]

    app.register_blueprint(auth)

    app.register_blueprint(api)

    return app


app = create_app()

if __name__ == "__main__":

    app.run(debug=True)
