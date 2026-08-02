class Portfolio:
    """
    Represents a trader's cash and stock holdings.
    """

    def __init__(self, starting_cash):
        self.cash = starting_cash

        # Symbol -> number of shares
        self.holdings = {}


    def buy(self, symbol, quantity, price):
        """
        Adds shares and removes cash.
        """

        cost = quantity * price

        if cost > self.cash:
            raise ValueError("Insufficient funds")

        self.cash -= cost

        if symbol not in self.holdings:
            self.holdings[symbol] = 0

        self.holdings[symbol] += quantity



    def sell(self, symbol, quantity, price):
        """
        Removes shares and adds cash.
        """

        if symbol not in self.holdings:
            raise ValueError("No shares owned")

        if self.holdings[symbol] < quantity:
            raise ValueError("Not enough shares")

        self.holdings[symbol] -= quantity

        self.cash += quantity * price



    def get_position(self, symbol):
        """
        Returns number of shares owned.
        """

        return self.holdings.get(symbol, 0)