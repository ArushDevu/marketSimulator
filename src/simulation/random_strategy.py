import random

from simulation.strategy import BaseStrategy



class RandomStrategy(BaseStrategy):
    """
    Randomly buys or sells.
    """


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        symbol = "AAPL"


        price = random.randint(
            95,
            105
        )


        quantity = random.randint(
            1,
            10
        )


        side = random.choice(
            ["BUY", "SELL"]
        )


        if side == "BUY":

            return self.trader.buy(
                symbol,
                quantity,
                price,
                exchange
            )


        else:

            return self.trader.sell(
                symbol,
                quantity,
                price,
                exchange
            )