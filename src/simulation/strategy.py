from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """

    category = "uncategorized"

    def __init__(self, trader, symbol="AAPL"):
        self.trader = trader
        self.symbol = symbol

        if getattr(trader, "category", None) is None:
            trader.category = self.category


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
