# LOGGER FOR MAIN.PY
from datetime import datetime
import pytz
import os
import traceback

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


class Logger:

    def getDatetime(self):

        dt = datetime.now(tz=pytz.UTC).replace(microsecond=0)

        dt_central = dt.astimezone(pytz.timezone('US/Central'))

        return datetime.strptime(dt_central.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")

    def log(self, log, log_type="info"):

        with open(f"{THIS_FOLDER}/logs/{log_type}_{str(self.getDatetime()).split(' ')[0].replace('-', '_')}.txt", "a") as f:

            f.write(f"{log}\n")

    def INFO(self, info):

        # LEVEL | DATE | MESSAGE
        log = f"INFO | {self.getDatetime()} | {info}"

        print(log)

        self.log(log)

    def WARNING(self, warning):

        # LEVEL | DATE | MESSAGE
        log = f"WARNING | {self.getDatetime()} | {warning}"

        print(log)

        self.log(log)

    def ERROR(self, error=None):

        # LEVEL:DATETIME
        if error == None:

            log = f"ERROR | {self.getDatetime()}"

        # LEVEL:DATETIME:MESSAGE
        else:

            log = f"ERROR | {self.getDatetime()} | {error}"

        print(log)

        tb = traceback.format_exc()

        print(tb)

        log = f"{log}\n{tb}"

        self.log(log, "error")

    def CRITICAL(self, error):

        # LEVEL:DATETIME:MESSAGE
        log = f"CRITICAL | {self.getDatetime()} | {error}"

        print(log)

        self.log(log, "error")
