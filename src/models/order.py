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
        timestamp
    ):
        
        # An order with zero or negative shares can't be executed
        if quantity <= 0:
            raise ValueError("Quantity must be positive!")
        
        # Limit orders need a price because execution depends on this value
        if order_type == "LIMIT" and price is None:
            raise ValueError("Limit orders need a price")
        
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
            raise ValueError("Fill quantity must be positive")
        
        if quantity > self.remaining_quantity:
            raise ValueError("Cannot fill more than remaining quantity")

        self.remaining_quantity -= quantity