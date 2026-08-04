from collections import deque

from engine.order_book import OrderBook
from engine.commission_model import CommissionModel


# How many completed trades to keep in the "recent trade tape" that's
# exposed via get_trade_history(). Bounded so a market that runs for a
# very long time doesn't grow this list forever.
TRADE_HISTORY_MAXLEN = 20_000


class MatchingEngine:
    """
    Coordinates order processing, records completed trades,
    and settles trades between traders.
    """

    def __init__(self, commission_model=None):

        # Symbol -> OrderBook
        self.order_books = {}

        self.trade_history = deque(maxlen=TRADE_HISTORY_MAXLEN)

        # Trades since the last drain_pending_trades() call.
        self._pending_trades = []

        # trader_id -> Trader object
        self.traders = {}

        self.total_trades_executed = 0

        # The current *simulation step*.
        self.current_step = 0

        # See engine.commission_model.CommissionModel -- applies a
        # real (if small) transaction cost to every settled trade.
        # Defaults to commission-free (0bps) so the Exchange/
        # MatchingEngine's own unit-level behavior (and the existing
        # test suite, which asserts exact settlement cash amounts)
        # stays frictionless unless a caller explicitly opts in.
        # runner.py opts in explicitly (2bps) to get the realistic
        # simulation described in the brief -- see Problem #7.
        self.commission_model = commission_model or CommissionModel(
            commission_bps=0.0
        )



    def set_current_step(self, step):
        self.current_step = step



    def drain_pending_trades(self):
        pending = self._pending_trades
        self._pending_trades = []
        return pending



    def _get_order_book(self, symbol):

        if symbol not in self.order_books:

            self.order_books[symbol] = OrderBook()


        return self.order_books[symbol]



    def register_trader(self, trader):
        """
        Adds a trader to the exchange.
        """

        existing = self.traders.get(trader.trader_id)

        if existing is not None and existing is not trader:
            raise ValueError(
                f"Trader ID {trader.trader_id} is already registered to "
                f"'{existing.name}' -- refusing to silently overwrite it "
                f"with '{trader.name}'. Trader IDs must be unique."
            )

        self.traders[trader.trader_id] = trader



    def submit_order(self, order):
        """
        Submits an order to the appropriate symbol's order book.
        """

        book = self._get_order_book(order.symbol)

        book.current_step = self.current_step

        expired_orders = book.remove_expired_orders()

        for expired_order in expired_orders:
            self._release_reservation(expired_order)


        trades = book.process_order(order)


        for trade in trades:

            buyer_id = trade.buy_order.trader_id
            seller_id = trade.sell_order.trader_id


            if (
                buyer_id in self.traders
                and seller_id in self.traders
            ):

                self.settle_trade(trade)


        self.trade_history.extend(trades)
        self._pending_trades.extend(trades)
        self.total_trades_executed += len(trades)


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

            trader.portfolio.release_cash(
                order.remaining_quantity * order.reservation_price
            )

        else:

            trader.portfolio.release_shares(
                order.symbol,
                order.remaining_quantity
            )



    def settle_trade(self, trade):
        """
        Updates buyer and seller portfolios after a trade, including
        commission (see engine.commission_model.CommissionModel).
        """

        buyer = self.traders[
            trade.buy_order.trader_id
        ]

        seller = self.traders[
            trade.sell_order.trader_id
        ]


        buyer.portfolio.release_cash(
            trade.quantity * trade.buy_order.reservation_price
        )

        seller.portfolio.release_shares(
            trade.sell_order.symbol,
            trade.quantity
        )


        buyer.portfolio.buy(
            trade.buy_order.symbol,
            trade.quantity,
            trade.price
        )

        seller.portfolio.sell(
            trade.sell_order.symbol,
            trade.quantity,
            trade.price
        )

        fee = self.commission_model.calculate_fee(
            trade.price,
            trade.quantity
        )

        if fee > 0:
            buyer.portfolio.charge_fee(fee)
            seller.portfolio.charge_fee(fee)



    def get_trade_history(self):
        return list(self.trade_history)



    def get_best_bid(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_best_bid()



    def get_best_ask(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_best_ask()



    def get_order_book_depth(self, symbol="AAPL"):
        return self._get_order_book(symbol).get_order_book_depth()



    def estimate_market_fill(self, symbol, side, quantity):
        return self._get_order_book(symbol).estimate_market_fill(
            side,
            quantity
        )
