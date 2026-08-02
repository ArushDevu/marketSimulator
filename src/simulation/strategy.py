from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """

    def __init__(self, trader):
        self.trader = trader


    @abstractmethod
    def generate_orders(
        self,
        exchange,
        market_data
    ):
        """
        Generate one or more orders.
        """
        pass