import random

from simulation.strategy import BaseStrategy



class RandomStrategy(BaseStrategy):
    """
    Randomly buys or sells around the current market price.

    No behavioral changes here -- this strategy already used `return
    None` consistently for its no-attempt branches. Its previous
    apparent "edge" over professional strategies (Problem #7) came
    from the *matching engine* being frictionless (fixed centrally in
    engine.commission_model.CommissionModel -- see matching_engines.py)
    rather than from anything wrong in this file: with real
    commissions in place, a strategy with no genuine informational
    edge now bleeds a small, realistic cost every trade instead of
    trading for free.
    """

    category = "random"


    def generate_orders(
        self,
        exchange,
        market_data=None
    ):

        current_price = (
            market_data.get_latest_price(self.symbol)
            if market_data is not None
            else None
        )


        if current_price is None:
            current_price = 100


        price = random.gauss(
            current_price,
            2
        )


        if price <= 0:
            return None


        side = random.choice(
            [
                "BUY",
                "SELL"
            ]
        )


        if side == "BUY":

            max_quantity = int(
                self.trader.get_cash() // price
            )

            if max_quantity <= 0:
                return None

            quantity = random.randint(
                1,
                min(10, max_quantity)
            )

            return self.trader.buy(
                self.symbol,
                quantity,
                price,
                exchange
            )


        else:

            shares = self.trader.get_position(
                self.symbol
            )

            if shares <= 0:
                return None

            quantity = random.randint(
                1,
                min(10, shares)
            )

            return self.trader.sell(
                self.symbol,
                quantity,
                price,
                exchange
            )
