import heapq

from models.trade import Trade
from engine.price_level import PriceLevel


class OrderBook:
    """
    Stores active buy and sell orders (all for a single symbol)
    grouped by price levels.
    """

    def __init__(self):

        # Price -> PriceLevel
        self.buy_levels = {}

        # Price -> PriceLevel
        self.sell_levels = {}

        # Max heap for BUY prices
        # (stored as negative values because heapq is a min heap)
        self.buy_heap = []

        # Min heap for SELL prices
        self.sell_heap = []

        # Order ID -> Order
        # Allows fast order lookup for cancellation
        self.orders = {}

        # Used to generate unique trade IDs
        self.next_trade_id = 1

        # Current simulation step
        self.current_step = 0



    def process_order(self, order):
        """
        Processes a new order.

        Attempts to match against existing orders.
        Any remaining quantity is added to the book, unless it's a
        MARKET order: those never rest, since there's no price to
        rest them at. Whatever a market order can't fill immediately
        just goes unfilled.
        """

        if order.side == "BUY":

            trades = self._match_buy_order(order)


        elif order.side == "SELL":

            trades = self._match_sell_order(order)


        else:

            raise ValueError(
                "Order side must be BUY or SELL"
            )


        if not order.is_filled() and order.order_type != "MARKET":

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

                heapq.heappush(
                    self.buy_heap,
                    -order.price
                )

            self.buy_levels[order.price].add_order(order)


        else:

            if order.price not in self.sell_levels:
                self.sell_levels[order.price] = PriceLevel(order.price)

                heapq.heappush(
                    self.sell_heap,
                    order.price
                )

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



    def _get_best_bid_price(self):
        """
        Returns the highest BUY price using the heap.

        Stale prices are removed lazily.
        """

        while self.buy_heap:

            best_price = -self.buy_heap[0]

            if best_price in self.buy_levels:
                return best_price

            heapq.heappop(self.buy_heap)

        return None



    def _get_best_ask_price(self):
        """
        Returns the lowest SELL price using the heap.

        Stale prices are removed lazily.
        """

        while self.sell_heap:

            best_price = self.sell_heap[0]

            if best_price in self.sell_levels:
                return best_price

            heapq.heappop(self.sell_heap)

        return None



    def get_best_bid(self):
        """
        Returns highest priced BUY order.
        """

        best_price = self._get_best_bid_price()

        if best_price is None:
            return None

        return self.buy_levels[best_price].get_first_order()



    def get_best_ask(self):
        """
        Returns lowest priced SELL order.
        """

        best_price = self._get_best_ask_price()

        if best_price is None:
            return None

        return self.sell_levels[best_price].get_first_order()



    def estimate_market_fill(self, side, quantity):
        """
        Walks the resting book on the opposite side to estimate what
        it would cost (or fetch) to fill `quantity` right now, without
        actually mutating the book. Used for slippage-aware order
        sizing and for reserving a sensible amount of cash for market
        orders.

        Returns (average_price, fillable_quantity). If there's no
        liquidity at all, returns (None, 0).
        """

        if side == "BUY":
            price_levels = self.sell_levels
            ordered_prices = sorted(price_levels.keys())

        else:
            price_levels = self.buy_levels
            ordered_prices = sorted(price_levels.keys(), reverse=True)


        remaining = quantity
        total_value = 0


        for price in ordered_prices:

            if remaining <= 0:
                break

            available = price_levels[price].get_volume()

            take = min(available, remaining)

            total_value += take * price

            remaining -= take


        filled = quantity - remaining

        if filled <= 0:
            return (None, 0)

        return (total_value / filled, filled)



    def _create_trade(self, buy_order, sell_order, quantity, price):
        """
        Creates a trade at the resting ("maker") order's price,
        not the incoming ("taker") order's price.
        """

        trade = Trade(
            trade_id=self.next_trade_id,
            buy_order=buy_order,
            sell_order=sell_order,
            price=price,
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

        while not order.is_filled():

            best_price = self._get_best_ask_price()

            if best_price is None:
                break

            # Limit orders must respect price
            # Market orders always accept the best available sell price
            if (
                order.order_type == "LIMIT"
                and order.price < best_price
            ):
                break


            level = self.sell_levels[best_price]

            best_sell = level.get_first_order()


            trade_quantity = min(
                order.remaining_quantity,
                best_sell.remaining_quantity
            )


            # best_sell is the resting (maker) order, so the trade
            # executes at its price.
            trade = self._create_trade(
                buy_order=order,
                sell_order=best_sell,
                quantity=trade_quantity,
                price=best_sell.price
            )


            trades.append(trade)


            order.fill(trade_quantity)
            best_sell.fill(trade_quantity)


            if best_sell.is_filled():
                self.remove_order(best_sell)


        return trades



    def _match_sell_order(self, order):

        trades = []

        while not order.is_filled():

            best_price = self._get_best_bid_price()

            if best_price is None:
                break

            # Limit orders must respect price
            # Market orders always accept the best available buy price
            if (
                order.order_type == "LIMIT"
                and order.price > best_price
            ):
                break


            level = self.buy_levels[best_price]

            best_buy = level.get_first_order()


            trade_quantity = min(
                order.remaining_quantity,
                best_buy.remaining_quantity
            )


            # best_buy is the resting (maker) order, so the trade
            # executes at its price.
            trade = self._create_trade(
                buy_order=best_buy,
                sell_order=order,
                quantity=trade_quantity,
                price=best_buy.price
            )


            trades.append(trade)


            order.fill(trade_quantity)
            best_buy.fill(trade_quantity)


            if best_buy.is_filled():
                self.remove_order(best_buy)


        return trades



    def remove_expired_orders(self):
        """
        Removes orders that have passed their expiry step.

        Returns the list of orders that were removed so callers
        (e.g. MatchingEngine) can release any reserved cash/shares
        that were held for them.
        """

        expired_orders = []


        for order in list(self.orders.values()):

            if order.is_expired(self.current_step):

                expired_orders.append(order)



        for order in expired_orders:

            self.remove_order(order)


        return expired_orders


    def get_order_book_depth(self):
        """
        Returns current market depth.

        BUY prices are sorted highest -> lowest.
        SELL prices are sorted lowest -> highest.
        """

        return {
            "buy": {
                price: self.buy_levels[price].get_volume()
                for price in sorted(
                    self.buy_levels.keys(),
                    reverse=True
                )
            },

            "sell": {
                price: self.sell_levels[price].get_volume()
                for price in sorted(
                    self.sell_levels.keys()
                )
            }
        }
