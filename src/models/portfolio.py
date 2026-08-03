class Portfolio:
    """
    Represents a trader's cash and stock holdings.
    """

    def __init__(self, starting_cash):

        self.cash = starting_cash

        # Save for future PnL calculations
        self.starting_cash = starting_cash

        # Symbol -> number of shares
        self.holdings = {}

        # Reserved cash for outstanding BUY orders
        self.reserved_cash = 0

        # Symbol -> reserved shares for outstanding SELL orders
        self.reserved_holdings = {}


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


    def add_position(self, symbol, quantity):
        """
        Adds starting shares without affecting cash.
        """

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if symbol not in self.holdings:
            self.holdings[symbol] = 0

        self.holdings[symbol] += quantity


    #
    # Reservation methods
    #

    def reserve_cash(self, amount):
        """
        Reserves cash for a BUY order.
        """

        available_cash = self.cash - self.reserved_cash

        if amount > available_cash:
            return False

        self.reserved_cash += amount

        return True


    def release_cash(self, amount):
        """
        Releases reserved cash.
        """

        self.reserved_cash -= amount

        if self.reserved_cash < 0:
            self.reserved_cash = 0


    def reserve_shares(self, symbol, quantity):
        """
        Reserves shares for a SELL order.
        """

        owned = self.get_position(symbol)

        reserved = self.reserved_holdings.get(symbol, 0)

        available = owned - reserved

        if quantity > available:
            return False

        self.reserved_holdings[symbol] = reserved + quantity

        return True


    def release_shares(self, symbol, quantity):
        """
        Releases reserved shares.
        """

        if symbol not in self.reserved_holdings:
            return

        self.reserved_holdings[symbol] -= quantity

        if self.reserved_holdings[symbol] <= 0:
            del self.reserved_holdings[symbol]


    def get_holdings_value(self, prices):
        """
        Returns the total market value of all holdings.

        prices:
            Dictionary mapping symbols to current prices.
        """

        total = 0

        for symbol, quantity in self.holdings.items():

            if symbol in prices:
                total += quantity * prices[symbol]

        return total


    def get_total_value(self, prices):
        """
        Returns total portfolio value.
        """

        return self.cash + self.get_holdings_value(prices)
