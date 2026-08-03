from simulation.market_data import MarketData


class MarketSimulator:
    def __init__(self, exchange, symbols=None, starting_prices=None):
        self.exchange = exchange
        self.symbols = symbols or ["AAPL"]
        self.strategies = []
        self.trade_history = []
        self.last_trade_index = 0
        self.market_data = MarketData(symbols=self.symbols, starting_prices=starting_prices)
        self.pnl_history = {}
        self.return_history = {}
        self.equity_history = {}
        self.starting_values = {}
        
        

    def add_strategy(self, strategy):
        self.strategies.append(strategy)
        trader = strategy.trader

        self.pnl_history[trader.name] = []
        self.return_history[trader.name] = []
        self.equity_history[trader.name] = []

        # Value using every symbol's current fair price, not just one
        # hardcoded symbol -- works correctly for multi-symbol traders.
        
        starting_prices = {s: self.market_data.get_fair_price(s) for s in self.symbols}
        starting_value = trader.portfolio.get_total_value(starting_prices)
        self.starting_values[trader.name] = starting_value

        if trader.starting_value is None:
            trader.initialize_starting_value(starting_prices)




    def _get_order_flow_imbalance(self, symbol):
        
        depth = self.exchange.get_order_book_depth(symbol)
        buy_volume = sum(depth["buy"].values())
        sell_volume = sum(depth["sell"].values())
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return 0.0
        
        return (buy_volume - sell_volume) / total_volume




    def run_step(self):
        
        for symbol in self.symbols:
            imbalance = self._get_order_flow_imbalance(symbol)
            self.market_data.update_market_price(symbol, order_flow_imbalance=imbalance)

        for strategy in self.strategies:
            strategy.generate_orders(self.exchange, self.market_data)

        primary_symbol = self.symbols[0]
        bid = self.exchange.matching_engine.get_best_bid(primary_symbol)
        ask = self.exchange.matching_engine.get_best_ask(primary_symbol)

        print(
            "Step:", self.last_trade_index,
            "Trades:", len(self.exchange.get_trade_history()),
            "Bid:", bid.price if bid else None,
            "Ask:", ask.price if ask else None,
            "Last:", self.market_data.get_latest_price(primary_symbol)
        )

        all_trades = self.exchange.get_trade_history()
        new_trades = all_trades[self.last_trade_index:]
        
        self.trade_history.extend(new_trades)

        for trade in new_trades:
            self.market_data.record_trade(trade)

        self.last_trade_index = len(all_trades)

        current_prices = {}
        
        for symbol in self.symbols:
            price = self.market_data.get_latest_price(symbol)
            
            if price is None:
                price = self.market_data.get_fair_price(symbol)
            current_prices[symbol] = price

        for strategy in self.strategies:
            trader = strategy.trader
            pnl = trader.get_pnl(current_prices)
            net_worth = trader.get_net_worth(current_prices)

            self.pnl_history[trader.name].append(pnl)
            self.equity_history[trader.name].append(net_worth)

            starting_value = self.starting_values[trader.name]
            percentage_return = (pnl / starting_value) * 100
            self.return_history[trader.name].append(percentage_return)