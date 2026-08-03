from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """

    def __init__(self, trader, symbol="AAPL"):
        self.trader = trader
        self.symbol = symbol


    @abstractmethod
    def generate_orders(
        self,
        exchange,
        market_data=None
    ):
        """
        Generate one or more orders.
        """
        pass
