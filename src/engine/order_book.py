from models.trade import Trade


class OrderBook:
    """
    Stores active buy and sell orders and processes incoming orders.
    """

    def __init__(self):
        # Active buy orders (highest price first)
        self.buy_orders = []

        # Active sell orders (lowest price first)
        self.sell_orders = []

        # Used to generate unique trade IDs
        self.next_trade_id = 1


    def process_order(self, order):
        """
        Processes a new order.

        Attempts to match the order against existing orders.
        Any unfilled quantity is added to the order book.

        Returns:
            list: Trade objects created while matching.
        """

        if order.side == "BUY":
            trades = self._match_buy_order(order)

        elif order.side == "SELL":
            trades = self._match_sell_order(order)

        else:
            raise ValueError("Order side must be BUY or SELL")

        # If the order wasn't completely filled,
        # store the remaining quantity.
        if not order.is_filled():
            self._add_order(order)

        return trades


    def _add_order(self, order):
        """
        Adds an unmatched order to the correct side of the book.
        """

        if order.side == "BUY":
            self.buy_orders.append(order)

            # Highest price first, then earliest timestamp
            self.buy_orders.sort(
                key=lambda o: (-o.price, o.timestamp)
            )

        else:
            self.sell_orders.append(order)

            # Lowest price first, then earliest timestamp
            self.sell_orders.sort(
                key=lambda o: (o.price, o.timestamp)
            )


    def remove_order(self, order):
        """
        Removes an order from the book.
        """

        if order.side == "BUY":
            self.buy_orders.remove(order)

        else:
            self.sell_orders.remove(order)


    def get_best_bid(self):
        """
        Returns the highest buy order.
        """

        if not self.buy_orders:
            return None

        return self.buy_orders[0]


    def get_best_ask(self):
        """
        Returns the lowest sell order.
        """

        if not self.sell_orders:
            return None

        return self.sell_orders[0]


    def _create_trade(self, buy_order, sell_order, quantity):
        """
        Creates a Trade object for a successful match.
        """

        trade = Trade(
            trade_id=self.next_trade_id,
            buy_order=buy_order,
            sell_order=sell_order,
            price=sell_order.price,
            quantity=quantity,
            timestamp=max(buy_order.timestamp, sell_order.timestamp)
        )

        self.next_trade_id += 1

        return trade


    def _match_buy_order(self, order):
        """
        Matches a BUY order against existing SELL orders.
        """

        trades = []

        while (
            not order.is_filled()
            and self.sell_orders
        ):

            best_sell = self.sell_orders[0]

            # Stop if prices do not cross
            if order.price < best_sell.price:
                break

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
        """
        Matches a SELL order against existing BUY orders.
        """

        trades = []

        while (
            not order.is_filled()
            and self.buy_orders
        ):

            best_buy = self.buy_orders[0]

            # Stop if prices do not cross
            if order.price > best_buy.price:
                break

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