import random


class MarketData:
    """
    Stores historical market information
    and simulates external price movement.
    """


    def __init__(self):

        self.prices = []
        self.volumes = []

        # Starting market price
        self.current_price = 100



    def update_market_price(self):
        """
        Simulates external market movement.
        """

        movement = random.gauss(
            0,
            0.5
        )

        self.current_price += movement


        # Prevent unrealistic prices
        if self.current_price < 10:
            self.current_price = 10



    def record_trade(self, trade):
        """
        Records a completed trade.
        """

        self.prices.append(
            trade.price
        )

        self.volumes.append(
            trade.quantity
        )

        # Market follows executed trades
        self.current_price = trade.price



    def get_latest_price(self):
        """
        Returns current market price.
        """

        return self.current_price



    def get_recent_prices(self, count):
        """
        Returns the last N prices.
        """

        return self.prices[-count:]



    def get_total_volume(self):
        """
        Returns total traded volume.
        """

        return sum(self.volumes)



    def get_vwap(self):
        """
        Returns volume weighted average price.
        """

        if not self.prices:
            return None


        total_value = sum(
            price * volume
            for price, volume in zip(
                self.prices,
                self.volumes
            )
        )


        total_volume = sum(
            self.volumes
        )


        return total_value / total_volume