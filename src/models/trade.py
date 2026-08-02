class Trade:
    """
    Represents an executed trade between a buyer and a seller.
    """

    def __init__(
        self,
        trade_id,
        buy_order,
        sell_order,
        price,
        quantity,
        timestamp
    ):

        # A trade must involve a positive number of shares
        if quantity <= 0:
            raise ValueError("Trade quantity must be positive.")

        # Trades cannot occur at a zero or negative price
        if price <= 0:
            raise ValueError("Trade price must be positive.")

        # Ensure the correct order types are provided
        if buy_order.side != "BUY":
            raise ValueError("buy_order must be a BUY order.")

        if sell_order.side != "SELL":
            raise ValueError("sell_order must be a SELL order.")

        # Both orders must refer to the same stock
        if buy_order.symbol != sell_order.symbol:
            raise ValueError("Orders must have the same symbol.")

        self.trade_id = trade_id

        self.buy_order = buy_order
        self.sell_order = sell_order

        # Both orders share the same symbol
        self.symbol = buy_order.symbol

        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp


    def get_buyer(self):
        """
        Returns the buyer's trader ID.
        """
        return self.buy_order.trader_id


    def get_seller(self):
        """
        Returns the seller's trader ID.
        """
        return self.sell_order.trader_id


    def __repr__(self):
        """
        Returns a readable representation of the trade.
        """

        return (
            f"Trade("
            f"id={self.trade_id}, "
            f"symbol='{self.symbol}', "
            f"price={self.price}, "
            f"quantity={self.quantity}, "
            f"buyer={self.buy_order.trader_id}, "
            f"seller={self.sell_order.trader_id}"
            f")"
        )