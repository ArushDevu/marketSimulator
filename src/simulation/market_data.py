class MarketData:
    """
    Stores historical market information.
    """


    def __init__(self):

        self.prices = []
        self.volumes = []



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



    def get_latest_price(self):
        """
        Returns most recent trade price.
        """

        if not self.prices:
            return None

        return self.prices[-1]



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