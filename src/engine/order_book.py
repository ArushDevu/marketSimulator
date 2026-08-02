from models.trade import Trade
from engine.price_level import PriceLevel


class OrderBook:
    """
    Stores active buy and sell orders grouped by price levels.
    """

    def __init__(self):

        # Price -> PriceLevel
        self.buy_levels = {}

        # Price -> PriceLevel
        self.sell_levels = {}

        # Order ID -> Order
        # Allows fast order lookup for cancellation
        self.orders = {}

        # Used to generate unique trade IDs
        self.next_trade_id = 1



    def process_order(self, order):
        """
        Processes a new order.

        Attempts to match against existing orders.
        Any remaining quantity is added to the book.
        """

        if order.side == "BUY":
            trades = self._match_buy_order(order)

        elif order.side == "SELL":
            trades = self._match_sell_order(order)

        else:
            raise ValueError("Order side must be BUY or SELL")


        if not order.is_filled():
            self._add_order(order)


        return trades



    def _add_order(self, order):
        """
        Adds an unmatched order to its price level.
        """

        # Store for cancellation lookup
        self.orders[order.order_id] = order


        if order.side == "BUY":

            if order.price not in self.buy_levels:
                self.buy_levels[order.price] = PriceLevel(order.price)

            self.buy_levels[order.price].add_order(order)


        else:

            if order.price not in self.sell_levels:
                self.sell_levels[order.price] = PriceLevel(order.price)

            self.sell_levels[order.price].add_order(order)



    def remove_order(self, order):
        """
        Removes an order from its price level.
        """

        if order.side == "BUY":
            level = self.buy_levels[order.price]

        else:
            level = self.sell_levels[order.price]


        level.remove_order(order)


        # Remove from order lookup
        if order.order_id in self.orders:
            del self.orders[order.order_id]


        # Remove empty price levels
        if len(level.orders) == 0:

            if order.side == "BUY":
                del self.buy_levels[order.price]

            else:
                del self.sell_levels[order.price]



    def cancel_order(self, order_id):
        """
        Cancels an active order.

        Returns:
            True if cancelled successfully
            False if order does not exist
        """

        if order_id not in self.orders:
            return False


        order = self.orders[order_id]

        self.remove_order(order)

        return True



    def get_best_bid(self):
        """
        Returns highest priced BUY order.
        """

        if not self.buy_levels:
            return None

        best_price = max(self.buy_levels.keys())

        return self.buy_levels[best_price].get_first_order()



    def get_best_ask(self):
        """
        Returns lowest priced SELL order.
        """

        if not self.sell_levels:
            return None

        best_price = min(self.sell_levels.keys())

        return self.sell_levels[best_price].get_first_order()



    def _create_trade(self, buy_order, sell_order, quantity):

        trade = Trade(
            trade_id=self.next_trade_id,
            buy_order=buy_order,
            sell_order=sell_order,
            price=sell_order.price,
            quantity=quantity,
            timestamp=max(
                buy_order.timestamp,
                sell_order.timestamp
            )
        )

        self.next_trade_id += 1

        return trade



    def _match_buy_order(self, order):

        trades = []

        while not order.is_filled() and self.sell_levels:

            best_price = min(self.sell_levels.keys())

            if order.price < best_price:
                break


            level = self.sell_levels[best_price]

            best_sell = level.get_first_order()


            trade_quantity = min(
                order.remaining_quantity,
                best_sell.remaining_quantity
            )


            trade = self._create_trade(
                buy_order=order,
                sell_order=best_sell,
                quantity=trade_quantity
            )


            trades.append(trade)


            order.fill(trade_quantity)
            best_sell.fill(trade_quantity)


            if best_sell.is_filled():
                self.remove_order(best_sell)


        return trades



    def _match_sell_order(self, order):

        trades = []

        while not order.is_filled() and self.buy_levels:

            best_price = max(self.buy_levels.keys())

            if order.price > best_price:
                break


            level = self.buy_levels[best_price]

            best_buy = level.get_first_order()


            trade_quantity = min(
                order.remaining_quantity,
                best_buy.remaining_quantity
            )


            trade = self._create_trade(
                buy_order=best_buy,
                sell_order=order,
                quantity=trade_quantity
            )


            trades.append(trade)


            order.fill(trade_quantity)
            best_buy.fill(trade_quantity)


            if best_buy.is_filled():
                self.remove_order(best_buy)


        return trades