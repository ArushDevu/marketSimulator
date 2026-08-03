class Order:
    """
    Represents a buy or sell request submitted to the exchange.
    """

    def __init__(
        self,
        order_id,
        trader_id,
        symbol,
        side,
        order_type,
        price,
        quantity,
        timestamp,
        expiry_step=None,
        reservation_price=None
    ):

        # An order with zero or negative shares can't be executed
        if quantity <= 0:
            raise ValueError("Quantity must be positive!")

        # Only allow supported order types
        if order_type not in ["LIMIT", "MARKET"]:
            raise ValueError(
                "Order type must be LIMIT or MARKET"
            )

        # Limit orders need a price
        if order_type == "LIMIT" and price is None:
            raise ValueError(
                "Limit orders need a price"
            )

        self.order_id = order_id
        self.trader_id = trader_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.price = price
        self.quantity = quantity

        # Tracks how many shares have not been filled yet
        self.remaining_quantity = quantity

        self.timestamp = timestamp

        # Simulation step when the order expires
        self.expiry_step = expiry_step

        # Per-share amount that was actually reserved in the trader's
        # portfolio when this order was submitted. For LIMIT orders this
        # is just the limit price. For MARKET orders (which have no
        # price up front) the caller must supply an estimated price,
        # since the portfolio needs *some* amount to lock up as
        # "reserved" until the order settles or is released.
        self.reservation_price = (
            reservation_price
            if reservation_price is not None
            else price
        )


    def is_filled(self):
        """
        Returns True if the entire order has been executed.
        """
        return self.remaining_quantity == 0


    def fill(self, quantity):
        """
        Reduces the remaining quantity after a trade is executed.
        """

        if quantity <= 0:
            raise ValueError(
                "Fill quantity must be positive"
            )

        if quantity > self.remaining_quantity:
            raise ValueError(
                "Cannot fill more than remaining quantity"
            )

        self.remaining_quantity -= quantity


    def is_expired(self, current_step):
        """
        Returns True if the order has expired.
        """

        if self.expiry_step is None:
            return False

        return current_step >= self.expiry_step
