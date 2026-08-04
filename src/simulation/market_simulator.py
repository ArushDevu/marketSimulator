from collections import deque

from simulation.market_data import MarketData
from engine.market_regime import MarketRegimeEngine


# How many recent steps of PnL/equity/return to keep per *tracked*
# trader, and per category. Bounded so a market running for a very
# long time doesn't grow this into a slow memory leak.
PER_TRADER_HISTORY_MAXLEN = 5_000

# Same reasoning for the simulator's own local trade log.
TRADE_HISTORY_MAXLEN = 20_000


class MarketSimulator:
    """
    Runs the market simulation across one or more symbols.

    Supports two levels of performance tracking:

    - Per-trader history (pnl_history / return_history / equity_history),
      kept only for traders added with track_history=True.

    - Per-category aggregate history (category_return_history), kept
      for *every* trader regardless of population size, grouped by
      Trader.category (e.g. "noise", "momentum", "market_maker").

    Activity tracking fix
    ----------------------
    The health-check "active rate" metric (last_step_category_activity
    / get_health_snapshot) used to count a strategy as active on a
    step only if generate_orders() returned a *truthy* value. Every
    strategy in this project returns an empty list `[]` whenever it
    submits a LIMIT order that rests unfilled -- the normal outcome
    for a passive quote, and not at all the same thing as "chose not
    to trade this step". `[]` is falsy, so a strategy that was
    genuinely placing orders every step but rarely getting an
    *immediate* fill (textbook market maker behavior) looked 0%
    active. Every strategy now returns None specifically to mean "no
    attempt this step", and returns its actual order-submission
    result (list of trades, possibly empty) otherwise. The activity
    check below was changed from `if result:` to
    `if result is not None:` to match -- see each strategy file's
    docstring (arbitrage.py has the fullest explanation) for the
    per-strategy side of this fix.

    Regime integration
    -------------------
    Price formation is now driven by a MarketRegimeEngine (see
    engine/market_regime.py) rather than a single stationary
    mean-reverting process, so trending/mean-reverting/calm/volatile/
    panic/recovery conditions actually occur and regime-aware
    strategies (momentum, mean reversion, market maker, arbitrage)
    have a genuine edge to detect in the regimes suited to them.
    """


    def __init__(
        self,
        exchange,
        symbols=None,
        starting_prices=None,
        regime_engine=None,
        regime_seed=None
    ):

        self.exchange = exchange

        self.symbols = symbols or ["AAPL"]

        self.strategies = []

        self.trade_history = deque(maxlen=TRADE_HISTORY_MAXLEN)

        # Real simulation-step counter, advanced once per run_step()
        # call regardless of how many orders get submitted within it.
        self._step_counter = 0

        self.market_data = MarketData(
            symbols=self.symbols,
            starting_prices=starting_prices
        )

        self.regime_engine = regime_engine or MarketRegimeEngine(
            symbols=self.symbols,
            seed=regime_seed
        )


        # Trader name -> deque of PnL / return / net worth values.
        # Only populated for traders added with track_history=True.
        self.pnl_history = {}
        self.return_history = {}
        self.equity_history = {}

        # Trader name -> starting portfolio value (kept for every
        # trader, tracked or not -- it's O(1) per trader and PnL/
        # category aggregation both need it).
        self.starting_values = {}

        # Names of traders with full per-step history tracked.
        self.tracked_traders = set()

        # category -> list of trader names in that category
        self.category_members = {}

        # category -> deque of mean percentage return, one entry per
        # simulation step, averaged across every trader in that
        # category (not just tracked ones).
        self.category_return_history = {}

        # category -> how many strategies in that category actually
        # submitted an order on the most recently completed step.
        self.last_step_category_activity = {}

        # category -> deque of trade counts per step (for turnover /
        # activity-rate analytics that need more than just the last
        # step's snapshot).
        self.category_activity_history = {}

        # trader_id -> category, kept in sync from add_strategy(). Used
        # to attribute trades to a category without re-scanning every
        # registered trader on every trade.
        self._trader_category_by_id = {}

        # category -> {"volume_bought", "volume_sold", "trades_bought",
        # "trades_sold", "notional_bought", "notional_sold"}, all
        # cumulative and *never trimmed* across the entire run -- see
        # market_data.py's docstring for why an unbounded counter is
        # the correct source of truth for cumulative accounting versus
        # summing a rolling-window history. This is what
        # AnalyticsEngine uses for per-category trade count, average
        # trade size, turnover, and market share.
        self.category_trade_stats = {}



    def _category_stats(self, category):

        return self.category_trade_stats.setdefault(
            category,
            {
                "volume_bought": 0,
                "volume_sold": 0,
                "trades_bought": 0,
                "trades_sold": 0,
                "notional_bought": 0.0,
                "notional_sold": 0.0,
            }
        )



    def add_strategy(self, strategy, track_history=True):
        """
        Adds a trading agent.

        track_history=False skips the per-step pnl/return/equity
        deques for this trader (still tracked in aggregate via
        category_return_history). Use this for large synthetic
        populations; leave it True for the handful of named traders
        you actually want individual charts/printouts for.
        """

        self.strategies.append(strategy)


        trader = strategy.trader

        category = getattr(trader, "category", None) or "uncategorized"
        trader.category = category

        self._trader_category_by_id[trader.trader_id] = category

        self.category_members.setdefault(category, []).append(trader.name)

        if category not in self.category_return_history:
            self.category_return_history[category] = deque(
                maxlen=PER_TRADER_HISTORY_MAXLEN
            )

        if category not in self.category_activity_history:
            self.category_activity_history[category] = deque(
                maxlen=PER_TRADER_HISTORY_MAXLEN
            )


        # Starting value at beginning of simulation, valued using
        # every symbol's current fair price.
        starting_prices = {
            symbol: self.market_data.get_fair_price(symbol)
            for symbol in self.symbols
        }


        starting_value = trader.portfolio.get_total_value(
            starting_prices
        )


        self.starting_values[
            trader.name
        ] = starting_value


        if trader.starting_value is None:

            trader.initialize_starting_value(
                starting_prices
            )


        if track_history:

            self.tracked_traders.add(trader.name)

            self.pnl_history[
                trader.name
            ] = deque(maxlen=PER_TRADER_HISTORY_MAXLEN)

            self.return_history[
                trader.name
            ] = deque(maxlen=PER_TRADER_HISTORY_MAXLEN)

            self.equity_history[
                trader.name
            ] = deque(maxlen=PER_TRADER_HISTORY_MAXLEN)



    def _get_order_flow_imbalance(self, symbol):
        """
        Computes how lopsided the resting order book is for a symbol:
        +1 means entirely buy pressure, -1 means entirely sell
        pressure, 0 means balanced (or no orders at all).
        """

        depth = self.exchange.get_order_book_depth(symbol)

        buy_volume = sum(depth["buy"].values())
        sell_volume = sum(depth["sell"].values())

        total_volume = buy_volume + sell_volume

        if total_volume == 0:
            return 0.0

        return (buy_volume - sell_volume) / total_volume



    def run_step(self, verbose=True):
        """
        Runs one simulation step across every symbol.
        """

        self._step_counter += 1
        self.exchange.set_current_step(self._step_counter)

        for symbol in self.symbols:

            imbalance = self._get_order_flow_imbalance(symbol)

            regime_params = self.regime_engine.step(symbol)

            self.market_data.update_market_price(
                symbol,
                order_flow_imbalance=imbalance,
                regime_params=regime_params
            )


        # Track, per category, how many strategies actually submitted
        # an order this step. See the class docstring for why this
        # checks `is not None` rather than truthiness.
        category_activity = {}

        for strategy in self.strategies:

            result = strategy.generate_orders(
                self.exchange,
                self.market_data
            )

            if result is not None:

                category = strategy.trader.category

                category_activity[category] = (
                    category_activity.get(category, 0) + 1
                )

        self.last_step_category_activity = category_activity

        for category in self.category_members:

            self.category_activity_history[category].append(
                category_activity.get(category, 0)
            )


        primary_symbol = self.symbols[0]

        if verbose:

            bid = self.exchange.matching_engine.get_best_bid(primary_symbol)
            ask = self.exchange.matching_engine.get_best_ask(primary_symbol)

            print(
                "Step:",
                self._step_counter,
                "Trades:",
                self.exchange.get_total_trades_executed(),
                "Bid:",
                bid.price if bid else None,
                "Ask:",
                ask.price if ask else None,
                "Last:",
                self.market_data.get_latest_price(primary_symbol),
                "Regime:",
                self.regime_engine.get_current_regime(primary_symbol)
            )


        new_trades = self.exchange.drain_pending_trades()

        self.trade_history.extend(new_trades)

        for trade in new_trades:

            self.market_data.record_trade(
                trade
            )

            buyer_category = self._trader_category_by_id.get(
                trade.get_buyer()
            )

            if buyer_category is not None:

                stats = self._category_stats(buyer_category)
                stats["volume_bought"] += trade.quantity
                stats["trades_bought"] += 1
                stats["notional_bought"] += trade.price * trade.quantity

            seller_category = self._trader_category_by_id.get(
                trade.get_seller()
            )

            if seller_category is not None:

                stats = self._category_stats(seller_category)
                stats["volume_sold"] += trade.quantity
                stats["trades_sold"] += 1
                stats["notional_sold"] += trade.price * trade.quantity


        current_prices = {}

        for symbol in self.symbols:

            price = self.market_data.get_latest_price(symbol)

            if price is None:
                price = self.market_data.get_fair_price(symbol)

            current_prices[symbol] = price


        # Accumulates this step's percentage returns per category, so
        # we can append one mean-return data point per category below
        # without needing to store every individual trader's history.
        category_step_returns = {}

        for strategy in self.strategies:

            trader = strategy.trader

            net_worth = trader.get_net_worth(
                current_prices
            )

            pnl = net_worth - trader.starting_value

            starting_value = self.starting_values[
                trader.name
            ]

            percentage_return = (
                (pnl / starting_value) * 100
                if starting_value
                else 0.0
            )


            if trader.name in self.tracked_traders:

                self.pnl_history[trader.name].append(pnl)
                self.equity_history[trader.name].append(net_worth)
                self.return_history[trader.name].append(percentage_return)


            category_step_returns.setdefault(
                trader.category, []
            ).append(percentage_return)


        for category, returns in category_step_returns.items():

            mean_return = sum(returns) / len(returns)

            self.category_return_history[category].append(mean_return)



    def get_health_snapshot(self, activity_window=50):
        """
        Cheap, population-size-independent summary you can print
        every N steps to sanity-check a large (e.g. 5,000-20,000
        agent) run without trying to plot every individual trader.

        activity_window: "active_pct" is averaged over the last N
        steps (category_activity_history) rather than read off a
        single step. A single-step snapshot is noisy for
        signal-driven strategies (arbitrage, mean-reversion, value)
        that might legitimately have zero qualifying signals on any
        one particular step while still trading regularly over a
        window -- exactly the ambiguity that made Problem #3 ("many
        categories remain inactive for long periods") hard to
        distinguish from "this category is now firing correctly, just
        not on this exact step" during validation. Market makers and
        noise traders, which act nearly every step by design, look
        the same either way; averaging mainly changes the picture for
        the sparser, threshold-driven strategies.

        Returns a dict with:
          - total_traders: total registered strategies
          - total_active_orders: resting orders across every symbol's book
          - total_trades_executed: cumulative trade count
          - total_volume: cumulative shares traded across every symbol
          - per_category: {category: {population, active_last_step,
            active_pct, mean_return_pct}}
        """

        per_category = {}

        for category, members in self.category_members.items():

            population = len(members)

            active_last_step = self.last_step_category_activity.get(
                category, 0
            )

            recent_activity = list(
                self.category_activity_history.get(category, [])
            )[-activity_window:]

            mean_active_per_step = (
                sum(recent_activity) / len(recent_activity)
                if recent_activity else active_last_step
            )

            history = self.category_return_history.get(category)

            mean_return = history[-1] if history else 0.0

            per_category[category] = {
                "population": population,
                "active_last_step": active_last_step,
                "active_pct": round(
                    100 * mean_active_per_step / population, 2
                ) if population else 0.0,
                "mean_return_pct": round(mean_return, 3),
                "window_trade_count": sum(recent_activity),
            }

        return {
            "step": self._step_counter,
            "total_traders": len(self.strategies),
            "total_active_orders": self.exchange.get_active_order_count(),
            "total_trades_executed": self.exchange.get_total_trades_executed(),
            "total_volume": self.market_data.get_total_volume(),
            "per_category": per_category,
        }



    def print_health_snapshot(self):
        """
        Pretty-prints get_health_snapshot() -- call this every N steps
        (e.g. every 100-500) for a large population run instead of
        printing/plotting every trader.
        """

        snapshot = self.get_health_snapshot()

        print("\n" + "=" * 60)
        print(f"Health check @ step {snapshot['step']}")
        print("=" * 60)
        print(f"Traders: {snapshot['total_traders']}   "
              f"Resting orders: {snapshot['total_active_orders']}   "
              f"Trades so far: {snapshot['total_trades_executed']}   "
              f"Volume so far: {snapshot['total_volume']:,}")
        print(f"{'Category':<15}{'Pop':>8}{'Active/step':>14}"
              f"{'Active %':>10}{'Mean Return %':>16}")

        for category, stats in sorted(snapshot["per_category"].items()):

            print(
                f"{category:<15}"
                f"{stats['population']:>8}"
                f"{stats['active_last_step']:>14}"
                f"{stats['active_pct']:>10}"
                f"{stats['mean_return_pct']:>16}"
            )

        print("=" * 60)
