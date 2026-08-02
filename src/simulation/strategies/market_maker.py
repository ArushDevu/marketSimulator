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

        if current_price is None:
            current_price = 100


        spread = 2

        buy_price = current_price - spread // 2
        sell_price = current_price + spread // 2


        max_quantity = 10


        #
        # BUY SIDE
        #

        max_buy_quantity = int(
            self.trader.get_cash() // buy_price
        )

        buy_quantity = min(
            max_quantity,
            max_buy_quantity
        )

        if buy_quantity > 0:

            self.trader.buy(
                symbol="AAPL",
                quantity=buy_quantity,
                price=buy_price,
                exchange=exchange
            )


        #
        # SELL SIDE
        #

        sell_quantity = min(
            max_quantity,
            self.trader.get_position("AAPL")
        )

        if sell_quantity > 0:

            self.trader.sell(
                symbol="AAPL",
                quantity=sell_quantity,
                price=sell_price,
                exchange=exchange
            )