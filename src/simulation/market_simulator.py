from simulation.market_data import MarketData


class MarketSimulator:
    """
    Runs the market simulation.
    """


    def __init__(self, exchange):

        self.exchange = exchange

        self.strategies = []

        self.trade_history = []

        # Number of exchange trades already processed
        self.last_trade_index = 0

        self.market_data = MarketData()



    def add_strategy(self, strategy):
        """
        Adds a trading agent.
        """

        self.strategies.append(strategy)



    def run_step(self):
        """
        Runs one simulation step.
        """

        for strategy in self.strategies:

            strategy.generate_orders(
                self.exchange,
                self.market_data
            )


        all_trades = self.exchange.get_trade_history()

        new_trades = all_trades[self.last_trade_index:]


        self.trade_history.extend(new_trades)


        for trade in new_trades:
            self.market_data.record_trade(trade)


        self.last_trade_index = len(all_trades)