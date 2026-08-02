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