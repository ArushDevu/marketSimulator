from engine.matching_engines import MatchingEngine


class Exchange:
    """
    Represents the stock exchange.
    Handles order IDs, timestamps, and market access.
    """


    def __init__(self):

        self.matching_engine = MatchingEngine()

        self.next_order_id = 1
        self.current_time = 0



    def get_next_order_id(self):
        """
        Generates unique order IDs.
        """

        order_id = self.next_order_id

        self.next_order_id += 1

        return order_id



    def get_timestamp(self):
        """
        Generates increasing timestamps.
        """

        self.current_time += 1

        return self.current_time



    def register_trader(self, trader):
        """
        Registers a trader with the exchange.
        """

        self.matching_engine.register_trader(trader)



    def get_best_bid(self):
        """
        Returns highest buy order.
        """

        return self.matching_engine.get_best_bid()



    def get_best_ask(self):
        """
        Returns lowest sell order.
        """

        return self.matching_engine.get_best_ask()



    def get_trade_history(self):
        """
        Returns completed trades.
        """

        return self.matching_engine.get_trade_history()



    def cancel_order(self, order_id):
        """
        Cancels an active order.
        """

        return self.matching_engine.cancel_order(order_id)



    def get_order_book_depth(self):
        return self.matching_engine.get_order_book_depth()
