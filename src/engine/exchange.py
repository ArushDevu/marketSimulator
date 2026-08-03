from engine.matching_engines import MatchingEngine


class Exchange:
    
    def __init__(self):
        self.matching_engine = MatchingEngine()
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


    def get_best_bid(self, symbol="AAPL"):
        return self.matching_engine.get_best_bid(symbol)


    def get_best_ask(self, symbol="AAPL"):
        return self.matching_engine.get_best_ask(symbol)

    def get_trade_history(self):
        return self.matching_engine.get_trade_history()


    def cancel_order(self, order_id):
        return self.matching_engine.cancel_order(order_id)


    def get_order_book_depth(self, symbol="AAPL"):
        return self.matching_engine.get_order_book_depth(symbol)


    def estimate_market_fill(self, symbol, side, quantity):
        """Estimates avg execution price & fillable qty for a market
        order of the given size, without submitting it."""
        
        return self.matching_engine.estimate_market_fill(symbol, side, quantity)