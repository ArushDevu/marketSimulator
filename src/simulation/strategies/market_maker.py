from simulation.strategy import Strategy


class MarketMaker(Strategy):
    """
    Places buy and sell orders around the current market price.
    """

    def generate_orders(self, exchange):

        latest_price = exchange.market_data.get_latest_price()

        if latest_price is None:
            latest_price = 100


        spread = 1


        buy_price = latest_price - spread
        sell_price = latest_price + spread


        quantity = 5


        self.trader.buy(
            symbol="AAPL",
            quantity=quantity,
            price=buy_price,
            exchange=exchange
        )


        self.trader.sell(
            symbol="AAPL",
            quantity=quantity,
            price=sell_price,
            exchange=exchange
        )