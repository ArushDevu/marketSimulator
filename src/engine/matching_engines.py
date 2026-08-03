from engine.order_book import OrderBook


class MatchingEngine:
    
    """
    Owns one OrderBook per symbol, so different stocks never match
    against each other.
    """

    def __init__(self):
        self.order_books = {}   # symbol -> OrderBook
        self.trade_history = []
        self.traders = {}



    def _get_order_book(self, symbol):
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook()
        return self.order_books[symbol]



    def register_trader(self, trader):
        self.traders[trader.trader_id] = trader



    def submit_order(self, order):
        book = self._get_order_book(order.symbol)
        book.current_step = order.timestamp

        expired_orders = book.remove_expired_orders()
        
        for expired_order in expired_orders:
            self._release_reservation(expired_order)

        trades = book.process_order(order)

        for trade in trades:
            buyer_id = trade.buy_order.trader_id
            seller_id = trade.sell_order.trader_id
            
            if buyer_id in self.traders and seller_id in self.traders:
                self.settle_trade(trade)

        self.trade_history.extend(trades)

        # MARKET orders never rest. If one couldn't be fully filled
        # right now, release whatever was reserved for the remainder.
        
        if order.order_type == "MARKET" and not order.is_filled():
            self._release_reservation(order)

        return trades



    def cancel_order(self, order_id):
        
        for book in self.order_books.values():
            
            if order_id in book.orders:
                order = book.orders[order_id]
                cancelled = book.cancel_order(order_id)
                
                if cancelled:
                    self._release_reservation(order)
                    
                return cancelled
            
        return False



    def _release_reservation(self, order):
        trader = self.traders.get(order.trader_id)
        
        if trader is None:
            return
        
        if order.side == "BUY":
            trader.portfolio.release_cash(order.remaining_quantity * order.reservation_price)
        
        else:
            trader.portfolio.release_shares(order.symbol, order.remaining_quantity)



    def settle_trade(self, trade):
        
        buyer = self.traders[trade.buy_order.trader_id]
        seller = self.traders[trade.sell_order.trader_id]

        # Release based on each order's original reservation amount,
        # not the trade price, so nothing gets permanently stuck.
        
        buyer.portfolio.release_cash(trade.quantity * trade.buy_order.reservation_price)
        seller.portfolio.release_shares(trade.sell_order.symbol, trade.quantity)

        buyer.portfolio.buy(trade.buy_order.symbol, trade.quantity, trade.price)
        seller.portfolio.sell(trade.sell_order.symbol, trade.quantity, trade.price)




    def get_trade_history(self):
        return self.trade_history



    def get_best_bid(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_best_bid()



    def get_best_ask(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_best_ask()
    
    

    def get_order_book_depth(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_order_book_depth()
    
    

    def estimate_market_fill(self, symbol, side, quantity):
        return self._get_order_book(symbol).estimate_market_fill(side, quantity)