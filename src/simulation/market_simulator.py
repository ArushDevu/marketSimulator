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


        # Trader name -> list of PnL values
        self.pnl_history = {}


        # Trader name -> list of percentage returns
        self.return_history = {}


        # Trader name -> list of net worth values
        self.equity_history = {}


        # Trader name -> starting portfolio value
        self.starting_values = {}



    def add_strategy(self, strategy):
        """
        Adds a trading agent.
        """

        self.strategies.append(strategy)


        trader = strategy.trader


        self.pnl_history[
            trader.name
        ] = []


        self.return_history[
            trader.name
        ] = []


        self.equity_history[
            trader.name
        ] = []



        # Starting value at beginning of simulation
        latest_price = 100


        starting_value = (
            trader.get_cash()
            +
            trader.get_position("AAPL")
            * latest_price
        )


        self.starting_values[
            trader.name
        ] = starting_value


        # Make sure the trader itself also knows its starting value,
        # since Trader.get_pnl() requires it and callers shouldn't
        # have to remember to set it up separately.
        if trader.starting_value is None:

            trader.initialize_starting_value(
                {"AAPL": latest_price}
            )




    def run_step(self):
        """
        Runs one simulation step.
        """

        self.market_data.update_market_price()


        for strategy in self.strategies:

            strategy.generate_orders(
                self.exchange,
                self.market_data
            )

        bid = self.exchange.matching_engine.get_best_bid()
        ask = self.exchange.matching_engine.get_best_ask()

        print(
            "Step:",
            self.last_trade_index,
            "Trades:",
            len(self.exchange.get_trade_history()),
            "Bid:",
            bid.price if bid else None,
            "Ask:",
            ask.price if ask else None,
            "Last:",
            self.market_data.get_latest_price()
        )



        all_trades = self.exchange.get_trade_history()


        new_trades = all_trades[
            self.last_trade_index:
        ]



        self.trade_history.extend(
            new_trades
        )



        for trade in new_trades:

            self.market_data.record_trade(
                trade
            )



        self.last_trade_index = len(all_trades)




        # Record trader performance
        latest_price = self.market_data.get_latest_price()


        if latest_price is not None:


            current_prices = {
                "AAPL": latest_price
            }



            for strategy in self.strategies:


                trader = strategy.trader



                pnl = trader.get_pnl(
                    current_prices
                )


                net_worth = trader.get_net_worth(
                    current_prices
                )



                # Store PnL history
                self.pnl_history[
                    trader.name
                ].append(
                    pnl
                )



                # Store equity history
                self.equity_history[
                    trader.name
                ].append(
                    net_worth
                )



                # Calculate percentage return

                starting_value = self.starting_values[
                    trader.name
                ]


                percentage_return = (
                    pnl / starting_value
                ) * 100



                self.return_history[
                    trader.name
                ].append(
                    percentage_return
                )
