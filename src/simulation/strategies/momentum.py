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


        quantity = 5


        if latest_price > oldest_price:

            return self.trader.buy(
                symbol="AAPL",
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        elif latest_price < oldest_price:

            return self.trader.sell(
                symbol="AAPL",
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        return []