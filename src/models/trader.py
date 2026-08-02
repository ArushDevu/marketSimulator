from models.portfolio import Portfolio
from models.order import Order


class Trader:
    """
    Represents a market participant.
    """


    def __init__(
        self,
        trader_id,
        name,
        starting_cash
    ):

        self.trader_id = trader_id
        self.name = name

        self.portfolio = Portfolio(
            starting_cash
        )



    def get_cash(self):
        """
        Returns available cash.
        """

        return self.portfolio.cash



    def get_position(self, symbol):
        """
        Returns owned shares.
        """

        return self.portfolio.get_position(symbol)



    def buy(
        self,
        symbol,
        quantity,
        price,
        exchange
    ):
        """
        Creates and submits a BUY order through the exchange.
        """

        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=exchange.get_timestamp()
        )

        return exchange.matching_engine.submit_order(order)



    def sell(
        self,
        symbol,
        quantity,
        price,
        exchange
    ):
        """
        Creates and submits a SELL order through the exchange.
        """

        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=exchange.get_timestamp()
        )

        return exchange.matching_engine.submit_order(order)