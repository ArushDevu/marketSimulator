from simulation.strategy import BaseStrategy


class MarketMakerStrategy(BaseStrategy):
    """
    Inventory-aware market maker.

    Provides liquidity while controlling inventory risk.
    """



    def generate_orders(
        self,
        exchange,
        market_data
    ):


        current_price = market_data.get_latest_price()


        if current_price is None:
            current_price = 100



        shares = self.trader.get_position(
            "AAPL"
        )

        cash = self.trader.get_cash()



        #
        # Inventory limits
        #

        max_inventory = 600
        min_inventory = 100



        #
        # Base spread
        #

        spread = 1



        #
        # Adjust spread based on inventory
        #

        if shares > max_inventory:

            # Too many shares
            # Make selling easier

            buy_price = current_price - 3
            sell_price = current_price + 0.5



        elif shares < min_inventory:

            # Too few shares
            # Make buying easier

            buy_price = current_price - 0.5
            sell_price = current_price + 3



        else:

            buy_price = current_price - spread / 2
            sell_price = current_price + spread / 2




        quantity = 10



        #
        # Submit buy order
        #

        if cash >= buy_price * quantity:

            self.trader.buy(
                symbol="AAPL",
                quantity=quantity,
                price=buy_price,
                exchange=exchange
            )



        #
        # Submit sell order
        #

        if shares >= quantity:

            self.trader.sell(
                symbol="AAPL",
                quantity=quantity,
                price=sell_price,
                exchange=exchange
            )