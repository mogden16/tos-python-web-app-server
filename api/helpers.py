import statistics


def maxDrawDown(value):

    try:

        # FIND MAX VALUE IN LIST
        max_value = max(value["Drawdowns"])

        # GET INDEX OF THAT VALUE
        max_index = value["Drawdowns"].index(max_value)

        # SEARCH FOR THE MIN FROM MAX INDEX TO THE END OF LIST
        min_value = min(value["Drawdowns"][max_index:])

        return round(
            max_value - min_value, 2)

    except:

        return 0


def sharpeRatio(value):

    try:

        standard_dev = statistics.stdev(value["Avg_ROV"])

        avg_trade_returns = statistics.mean(value["Avg_ROV"])

        return round(avg_trade_returns / standard_dev, 2)

    except:

        return 0
