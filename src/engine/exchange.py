from engine.matching_engines import MatchingEngine


class Exchange:
    """
    Represents the stock exchange.
    Handles order IDs, timestamps, and market access across symbols.
    """


    def __init__(self, commission_model=None):

        self.matching_engine = MatchingEngine(commission_model=commission_model)

        self.next_order_id = 1
        self.current_time = 0



    def get_next_order_id(self):

        order_id = self.next_order_id

        self.next_order_id += 1

        return order_id



    def get_timestamp(self):

        self.current_time += 1

        return self.current_time



    def register_trader(self, trader):
        self.matching_engine.register_trader(trader)



    def set_current_step(self, step):
        self.matching_engine.set_current_step(step)



    def get_current_step(self):
        return self.matching_engine.current_step



    def drain_pending_trades(self):
        return self.matching_engine.drain_pending_trades()



    def get_best_bid(self, symbol="AAPL"):
        return self.matching_engine.get_best_bid(symbol)



    def get_best_ask(self, symbol="AAPL"):
        return self.matching_engine.get_best_ask(symbol)



    def get_trade_history(self):
        return self.matching_engine.get_trade_history()



    def get_total_trades_executed(self):
        return self.matching_engine.total_trades_executed



    def cancel_order(self, order_id):
        return self.matching_engine.cancel_order(order_id)



    def get_order_book_depth(self, symbol="AAPL"):
        return self.matching_engine.get_order_book_depth(symbol)



    def estimate_market_fill(self, symbol, side, quantity):

        return self.matching_engine.estimate_market_fill(
            symbol,
            side,
            quantity
        )



    def get_registered_traders(self):
        """
        Returns every Trader registered with the exchange. Used by
        health-check / diagnostic reporting rather than by the
        matching path itself.
        """

        return list(self.matching_engine.traders.values())



    def get_active_order_count(self):
        """
        Total number of orders currently resting across every
        symbol's book -- a quick liquidity sanity check.
        """

        return sum(
            len(book.orders)
            for book in self.matching_engine.order_books.values()
        )
