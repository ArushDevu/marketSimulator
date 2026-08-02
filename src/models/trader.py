from models.portfolio import Portfolio


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