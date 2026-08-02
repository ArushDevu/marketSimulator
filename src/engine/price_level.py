class PriceLevel:
    """
    Represents all orders at a specific price.
    """

    def __init__(self, price):

        self.price = price

        # Orders waiting at this price
        # Maintains time priority (FIFO)
        self.orders = []


    def add_order(self, order):
        """
        Adds an order to this price level.
        """

        self.orders.append(order)



    def remove_order(self, order):
        """
        Removes an order from this price level.
        """

        self.orders.remove(order)



    def get_volume(self):
        """
        Returns total remaining quantity
        at this price.
        """

        total = 0

        for order in self.orders:
            total += order.remaining_quantity

        return total



    def get_first_order(self):
        """
        Returns the oldest order.
        """

        if not self.orders:
            return None

        return self.orders[0]