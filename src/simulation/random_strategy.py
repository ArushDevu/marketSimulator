import random
from simulation.strategy import Strategy



class RandomStrategy(Strategy):
    """
    Randomly buys or sells.
    """


    def generate_orders(self, exchange):

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