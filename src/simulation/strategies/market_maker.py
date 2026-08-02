from simulation.strategy import BaseStrategy


class MarketMakerStrategy(BaseStrategy):
    """
    Provides liquidity by placing buy and sell orders
    around the current market price.
    """


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        current_price = market_data.get_latest_price()


        # No market price yet
        # Start around a reasonable value
        if current_price is None:
            current_price = 100



        spread = 2


        buy_price = current_price - spread // 2
        sell_price = current_price + spread // 2


        quantity = 10



        # Place buy order
        self.trader.buy(
            symbol="AAPL",
            quantity=quantity,
            price=buy_price,
            exchange=exchange
        )



        # Place sell order
        self.trader.sell(
            symbol="AAPL",
            quantity=quantity,
            price=sell_price,
            exchange=exchange
        )