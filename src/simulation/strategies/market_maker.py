from simulation.strategy import BaseStrategy


class MarketMakerStrategy(BaseStrategy):
    """
    Inventory- and volatility-aware two-sided market maker.

    Two structural bugs in the original version explain Problem #1
    ("market makers almost never participate, yet consistently earn
    +26%"):

      1. generate_orders() called self.trader.buy(...) and
         self.trader.sell(...) every single step -- it genuinely WAS
         active every step -- but never returned the result.
         MarketSimulator's activity tracker only counts a strategy as
         "active" on a step if generate_orders() returns something
         truthy; a bare `None` return (the implicit return of a
         function with no `return` statement) meant every single
         quote this strategy placed was invisible to the "active
         rate" health metric, even though real orders were genuinely
         being submitted and genuinely being filled. Fixed below by
         returning the submitted orders.
      2. Because it requoted every step without ever cancelling the
         previous step's still-resting quotes, thousands of stale
         limit orders piled up in the book (only cleared by the
         20-step expiry), so its true "participation" also looked
         nothing like a real market maker's continuously-refreshed
         two-sided quote. Fixed below via cancel-and-replace.

    On top of the bug fixes, this version makes the *quoting itself*
    more realistic (Problems #5 and #11):
      - Spread widens with recent realized volatility (adverse
        selection protection -- a real MM pulls back / charges more
        when the market is choppy instead of quoting a fixed $1
        spread regardless of conditions).
      - Inventory skew: quotes shift continuously in proportion to
        how far inventory has drifted from a target, rather than
        flipping between three hard-coded regimes at fixed inventory
        thresholds. This is what actually creates the "inventory
        risk / drawdowns" realism Problem #5 asks for: a market maker
        that is long can't perfectly offload risk-free, so it must
        accept giving up edge (skewing its ask more attractively) to
        work the position down, and vice versa when short.
      - Quote size shrinks as inventory approaches its hard limit and
        as volatility rises, instead of always quoting a fixed size
        of 5 regardless of risk.
    """

    category = "market_maker"

    def __init__(
        self,
        trader,
        symbol="AAPL",
        base_spread_bps=15.0,
        volatility_spread_multiplier=8.0,
        max_inventory=200,
        target_inventory=100,
        base_quantity=5,
        skew_strength=1.5
    ):

        super().__init__(trader, symbol)

        # Base half-spread and how strongly recent realized
        # volatility widens it, in basis points of price.
        self.base_spread_bps = base_spread_bps
        self.volatility_spread_multiplier = volatility_spread_multiplier

        self.max_inventory = max_inventory
        self.target_inventory = target_inventory

        self.base_quantity = base_quantity
        self.skew_strength = skew_strength

        # Track our own currently-resting quote IDs so we can
        # cancel-and-replace each step instead of stacking new quotes
        # on top of stale ones.
        self._active_buy_order_id = None
        self._active_sell_order_id = None


    def _cancel_stale_quotes(self, exchange):

        if self._active_buy_order_id is not None:
            exchange.cancel_order(self._active_buy_order_id)
            self._active_buy_order_id = None

        if self._active_sell_order_id is not None:
            exchange.cancel_order(self._active_sell_order_id)
            self._active_sell_order_id = None


    def generate_orders(self, exchange, market_data):

        current_price = market_data.get_fair_price(self.symbol)

        if current_price is None:
            current_price = 100

        volatility = market_data.get_recent_volatility(self.symbol)

        # Cancel-and-replace: a real market maker continuously
        # refreshes its two-sided quote rather than leaving stale
        # prices resting indefinitely.
        self._cancel_stale_quotes(exchange)

        shares = self.trader.get_position(self.symbol)
        cash = self.trader.get_cash()

        # --- Adaptive spread ---
        # Base spread plus a volatility-scaled widening, expressed as
        # a fraction of price rather than a fixed dollar amount, so
        # it behaves sensibly across very different price levels too.
        spread_fraction = (
            self.base_spread_bps / 10_000
            + (volatility / current_price) * self.volatility_spread_multiplier
        )

        half_spread = current_price * spread_fraction / 2

        # --- Inventory skew ---
        # How far inventory has drifted from target, normalized by
        # the inventory limit. Positive => long => skew quotes to
        # encourage selling (raise bid less / drop ask more).
        inventory_deviation = (shares - self.target_inventory) / max(
            self.max_inventory, 1
        )

        skew = current_price * spread_fraction * self.skew_strength * inventory_deviation

        buy_price = round(current_price - half_spread - skew, 2)
        sell_price = round(current_price + half_spread - skew, 2)

        if buy_price <= 0:
            buy_price = 0.01

        # --- Risk-aware sizing ---
        # Shrink quote size as inventory nears its hard cap and as
        # volatility rises, instead of a fixed quantity regardless of
        # risk. Never fully stops quoting near the cap (a real MM
        # still makes a two-sided market, just smaller/skewed) unless
        # the hard cap is actually breached.
        inventory_room_buy = max(self.max_inventory - shares, 0)
        inventory_room_sell = max(shares, 0)

        vol_damping = 1.0 / (1.0 + volatility / max(current_price * 0.01, 1e-6))

        buy_quantity = max(
            1, int(min(self.base_quantity, inventory_room_buy) * vol_damping)
        )
        sell_quantity = max(
            1, int(min(self.base_quantity, inventory_room_sell) * vol_damping)
        )

        # IMPORTANT: "activity" for the health-check / analytics
        # system means "did this strategy submit an order", not "did
        # that order fill immediately". trader.buy()/trader.sell()
        # return an *empty* trades list (not None) whenever a LIMIT
        # order is accepted but rests unfilled -- which, for a
        # passive market maker quote, is the *normal, expected*
        # outcome most of the time. Returning that empty list
        # directly used to look identical to "chose not to act at
        # all" under a truthiness check. We track "attempted" (a
        # submission actually happened) separately from the trades
        # themselves, and return None only when neither side was
        # attempted -- see MarketSimulator.run_step's activity check.
        attempted = False
        trades = []

        if shares < self.max_inventory and cash >= buy_price * buy_quantity:

            buy_result = self.trader.buy(
                symbol=self.symbol,
                quantity=buy_quantity,
                price=buy_price,
                exchange=exchange
            )

            if buy_result is not None:

                attempted = True
                trades.extend(buy_result)

                # trader.buy() returns the list of *trades* generated
                # immediately; the resting order itself, if any
                # remains, is the most recently submitted order in
                # the book. Track it via the order-id counter so we
                # can cancel it next step even if it never fills.
                self._active_buy_order_id = exchange.next_order_id - 1

        if shares > 0:

            sell_result = self.trader.sell(
                symbol=self.symbol,
                quantity=sell_quantity,
                price=sell_price,
                exchange=exchange
            )

            if sell_result is not None:

                attempted = True
                trades.extend(sell_result)

                self._active_sell_order_id = exchange.next_order_id - 1

        if not attempted:
            return None

        return trades
