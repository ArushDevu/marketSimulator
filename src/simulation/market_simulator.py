from simulation.market_data import MarketData

class MarketSimulator:
    """
    Runs the market simulation.
    """


    def __init__(self, exchange):

        self.exchange = exchange

        self.strategies = []

        self.trade_history = []
        
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

            trades = strategy.generate_orders(
                self.exchange
            )


        trades = self.exchange.get_trade_history()

        self.trade_history.extend(trades)


        for trade in trades:
            self.market_data.record_trade(trade)