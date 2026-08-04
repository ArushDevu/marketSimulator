from models.portfolio import Portfolio
from models.order import Order


# How many *simulation steps* a resting order stays live before it
# expires. Deliberately based on the exchange's simulation-step clock
# (Exchange.get_current_step()), not on how many orders have been
# submitted -- the latter would make orders live for a shrinking
# fraction of real time as the trader population grows, since more
# traders means more orders submitted per actual step.
ORDER_EXPIRY_STEPS = 20


class Trader:
    """
    Represents a market participant.
    """


    def __init__(
        self,
        trader_id,
        name,
        starting_cash,
        category=None
    ):

        self.trader_id = trader_id
        self.name = name

        self.portfolio = Portfolio(
            starting_cash
        )

        # Recorded once before the simulation begins
        self.starting_value = None

        # Optional label (e.g. "noise", "momentum", "market_maker",
        # "institutional") used to aggregate stats across large
        # populations of traders where per-trader tracking/plotting
        # isn't practical. Purely descriptive -- nothing in the
        # matching/settlement path depends on it.
        self.category = category



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
        Creates and submits a LIMIT BUY order through the exchange.
        """

        cost = quantity * price

        # Reserve cash before submitting order
        if not self.portfolio.reserve_cash(cost):
            return None


        order_timestamp = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=order_timestamp,
            expiry_step=exchange.get_current_step() + ORDER_EXPIRY_STEPS
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
        Creates and submits a LIMIT SELL order through the exchange.
        """


        # Reserve shares before submitting order
        if not self.portfolio.reserve_shares(
            symbol,
            quantity
        ):
            return None


        order_timestamp = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=order_timestamp,
            expiry_step=exchange.get_current_step() + ORDER_EXPIRY_STEPS
        )


        return exchange.matching_engine.submit_order(order)



    def buy_market(
        self,
        symbol,
        quantity,
        exchange,
        market_data=None
    ):
        """
        Creates and submits a MARKET BUY order.

        Since a market order has no set price, we estimate the likely
        execution cost by walking the live order book first (falling
        back to the simulated fair value if the book is empty), then
        reserve a little extra (2%) to cover the price moving against
        us while the order is in flight.
        """

        estimated_price, _ = exchange.estimate_market_fill(
            symbol,
            "BUY",
            quantity
        )

        if estimated_price is None:

            estimated_price = (
                market_data.get_fair_price(symbol)
                if market_data is not None
                else None
            )

        if not estimated_price:
            estimated_price = 100


        reservation_price = estimated_price * 1.02

        cost = quantity * reservation_price


        if not self.portfolio.reserve_cash(cost):
            return None


        order_timestamp = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="MARKET",
            price=None,
            quantity=quantity,
            timestamp=order_timestamp,
            expiry_step=exchange.get_current_step() + ORDER_EXPIRY_STEPS,
            reservation_price=reservation_price
        )


        return exchange.matching_engine.submit_order(order)



    def sell_market(
        self,
        symbol,
        quantity,
        exchange
    ):
        """
        Creates and submits a MARKET SELL order.
        """

        if not self.portfolio.reserve_shares(
            symbol,
            quantity
        ):
            return None


        order_timestamp = exchange.get_timestamp()


        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="MARKET",
            price=None,
            quantity=quantity,
            timestamp=order_timestamp,
            expiry_step=exchange.get_current_step() + ORDER_EXPIRY_STEPS
        )


        return exchange.matching_engine.submit_order(order)
