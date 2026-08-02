class Strategy:
    """
    Base class for trading strategies.
    """


    def __init__(self, trader):
        self.trader = trader



    def generate_orders(self, exchange):
        """
        Generates orders.

        Must be implemented by subclasses.
        """

        raise NotImplementedError