from simulation.strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    Buys when price is trending upward.
    Sells when price is trending downward.
    """


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        prices = market_data.get_recent_prices(5)

        if len(prices) < 5:
            return []


        oldest_price = prices[0]
        latest_price = prices[-1]


        symbol = "AAPL"


        #
        # Uptrend -> Buy
        #

        if latest_price > oldest_price:

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
        # Downtrend -> Sell
        #

        elif latest_price < oldest_price:

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
