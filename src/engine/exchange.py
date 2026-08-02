from engine.matching_engines import MatchingEngine


class Exchange:
    """
    Represents the stock exchange.
    Handles order IDs and timestamps.
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