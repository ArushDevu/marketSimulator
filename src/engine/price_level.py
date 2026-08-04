class PriceLevel:
    """
    Represents all orders at a specific price.
    """

    def __init__(self, price):

        self.price = price
        self.orders = []


    def add_order(self, order):
        self.orders.append(order)


    def remove_order(self, order):
        self.orders.remove(order)


    def get_volume(self):

        total = 0

        for order in self.orders:
            total += order.remaining_quantity

        return total


    def get_first_order(self):

        if not self.orders:
            return None

        return self.orders[0]
