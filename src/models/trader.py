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

        # Recorded once before the simulation begins
        self.starting_value = None



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



    def initialize_starting_value(self, prices):
        """
        Records the trader's starting net worth.
        """

        self.starting_value = (
            self.portfolio.get_total_value(prices)
        )



    def get_net_worth(self, prices):
        """
        Returns current total net worth.
        """

        return self.portfolio.get_total_value(prices)



    def get_pnl(self, prices):
        """
        Returns profit and loss.
        """

        if self.starting_value is None:
            raise ValueError(
                "Starting value has not been initialized."
            )

        return (
            self.get_net_worth(prices)
            - self.starting_value
        )



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

        cost = quantity * price

        # Reserve cash before submitting order
        if not self.portfolio.reserve_cash(cost):
            return None


        current_step = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100
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


        # Reserve shares before submitting order
        if not self.portfolio.reserve_shares(
            symbol,
            quantity
        ):
            return None


        current_step = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100
        )


        return exchange.matching_engine.submit_order(order)
