from simulation.strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    Buys when the price has dropped meaningfully below its recent
    average (expecting it to bounce back up).
    Sells when the price has risen meaningfully above its recent
    average (expecting it to fall back down).
    """

    def __init__(self, trader, lookback=10, threshold=0.01):

        super().__init__(trader)

        # How many recent trade prices to average over
        self.lookback = lookback

        # Minimum % deviation from the average before acting,
        # to avoid trading on noise
        self.threshold = threshold


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        prices = market_data.get_recent_prices(self.lookback)

        if len(prices) < self.lookback:
            return []


        symbol = "AAPL"

        average_price = sum(prices) / len(prices)
        latest_price = prices[-1]

        if average_price == 0:
            return []

        deviation = (latest_price - average_price) / average_price


        #
        # Price is well below average -> expect it to revert upward -> buy
        #

        if deviation < -self.threshold:

            max_quantity = int(
                self.trader.get_cash() // latest_price
            )

            if max_quantity <= 0:
                return []

            quantity = min(5, max_quantity)

            return self.trader.buy(
                symbol=symbol,
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        #
        # Price is well above average -> expect it to revert downward -> sell
        #

        elif deviation > self.threshold:

            shares = self.trader.get_position(symbol)

            if shares <= 0:
                return []

            quantity = min(5, shares)

            return self.trader.sell(
                symbol=symbol,
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        return []
