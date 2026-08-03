import random

from simulation.strategy import BaseStrategy



class RandomStrategy(BaseStrategy):
    """
    Randomly buys or sells around the current market price.
    """


    def generate_orders(
        self,
        exchange,
        market_data=None
    ):

        #
        # Use current market price
        #

        current_price = (
            market_data.get_latest_price(self.symbol)
            if market_data is not None
            else None
        )


        # Simulation start price
        if current_price is None:
            current_price = 100



        #
        # Random trader submits slightly noisy orders
        #

        price = random.gauss(
            current_price,
            2
        )


        #
        # Prevent impossible prices
        #

        if price <= 0:
            return None



        side = random.choice(
            [
                "BUY",
                "SELL"
            ]
        )



        if side == "BUY":


            #
            # Buy only what we can afford
            #

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


            #
            # Sell only shares owned
            #

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
