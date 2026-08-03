from simulation.market_data import MarketData


class MarketSimulator:
    """
    Runs the market simulation across one or more symbols.
    """


    def __init__(self, exchange, symbols=None, starting_prices=None):

        self.exchange = exchange

        self.symbols = symbols or ["AAPL"]

        self.strategies = []

        self.trade_history = []

        # Number of exchange trades already processed
        self.last_trade_index = 0

        self.market_data = MarketData(
            symbols=self.symbols,
            starting_prices=starting_prices
        )


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



        # Starting value at beginning of simulation, valued using
        # every symbol's current fair price (not just one hardcoded
        # symbol), so this works correctly for multi-symbol traders.
        starting_prices = {
            symbol: self.market_data.get_fair_price(symbol)
            for symbol in self.symbols
        }


        starting_value = trader.portfolio.get_total_value(
            starting_prices
        )


        self.starting_values[
            trader.name
        ] = starting_value


        # Make sure the trader itself also knows its starting value,
        # since Trader.get_pnl() requires it and callers shouldn't
        # have to remember to set it up separately.
        if trader.starting_value is None:

            trader.initialize_starting_value(
                starting_prices
            )



    def _get_order_flow_imbalance(self, symbol):
        """
        Computes how lopsided the resting order book is for a symbol:
        +1 means entirely buy pressure, -1 means entirely sell
        pressure, 0 means balanced (or no orders at all).
        """

        depth = self.exchange.get_order_book_depth(symbol)

        buy_volume = sum(depth["buy"].values())
        sell_volume = sum(depth["sell"].values())

        total_volume = buy_volume + sell_volume

        if total_volume == 0:
            return 0.0

        return (buy_volume - sell_volume) / total_volume



    def run_step(self):
        """
        Runs one simulation step across every symbol.
        """

        # Let real resting order-book pressure push the fair price
        # around, on top of the usual random noise.
        for symbol in self.symbols:

            imbalance = self._get_order_flow_imbalance(symbol)

            self.market_data.update_market_price(
                symbol,
                order_flow_imbalance=imbalance
            )


        for strategy in self.strategies:

            strategy.generate_orders(
                self.exchange,
                self.market_data
            )


        primary_symbol = self.symbols[0]

        bid = self.exchange.matching_engine.get_best_bid(primary_symbol)
        ask = self.exchange.matching_engine.get_best_ask(primary_symbol)

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
            self.market_data.get_latest_price(primary_symbol)
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




        # Record trader performance, valuing every symbol at its
        # latest traded price (falling back to fair value for symbols
        # that haven't traded yet this run).
        current_prices = {}

        for symbol in self.symbols:

            price = self.market_data.get_latest_price(symbol)

            if price is None:
                price = self.market_data.get_fair_price(symbol)

            current_prices[symbol] = price


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
