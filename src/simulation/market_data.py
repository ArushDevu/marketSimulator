import random


# How many recent trades per symbol to retain for *lookback-based*
# reads (get_recent_prices, get_vwap-over-recent-window, etc). Kept
# as plain lists (not deques) because get_recent_prices() does
# frequent small tail slices from hot per-step, per-strategy code
# paths -- Python list slicing for a tail slice is O(count)
# regardless of the list's total length, so that stays cheap.
#
# IMPORTANT: this is a *rolling window for recency-based reads only*.
# It is deliberately NOT the source of truth for cumulative
# statistics like total volume or total trade count -- see
# total_volume / total_trade_count below. The original implementation
# used this trimmed list for get_total_volume() as well, which is
# the root cause of Problem #2 ("4.66 million trades executed, only
# ~33,000 shares traded"): total_trades_executed (in the matching
# engine) is a simple incrementing counter that never loses data, but
# get_total_volume() was summing this *trimmed* list, which only ever
# holds the most recent ~5,000-10,000 trades' worth of volume once a
# run exceeds that length. Over a run producing millions of trades,
# the reported "total volume" reflected only the last few thousand
# trades, while "total trades executed" reflected the true full-run
# count -- two numbers computed over completely different windows of
# the same run, which is why they looked wildly inconsistent despite
# both individually being computed correctly for what they measure.
PRICE_HISTORY_MAXLEN = 5_000


class MarketData:
    """
    Stores historical market information per symbol, and simulates
    external price movement that reacts to real order-book pressure
    (order flow imbalance) instead of being pure noise.

    The fair-value process is mean-reverting (Ornstein-Uhlenbeck
    style) by default, but every step's drift/volatility/reversion
    can be modulated by a `regime_params` dict (see
    engine.market_regime.MarketRegimeEngine) so the process can also
    trend, go calm, go volatile, or crash -- see update_market_price.
    """

    def __init__(
        self,
        symbols=None,
        starting_prices=None,
        impact_factor=0.15,
        reversion_strength=0.03,
        anchor_volatility=0.05,
        base_volatility=0.5
    ):

        symbols = symbols or ["AAPL"]
        starting_prices = starting_prices or {}

        self.symbols = list(symbols)

        # Symbol -> list of executed trade prices / volumes, TRIMMED
        # to a rolling recent window. Use for recency-based reads
        # only (get_recent_prices, get_vwap). See module docstring.
        self.prices = {symbol: [] for symbol in self.symbols}
        self.volumes = {symbol: [] for symbol in self.symbols}

        # Symbol -> cumulative totals across the *entire* run,
        # updated in O(1) per trade and never trimmed. This is the
        # source of truth for "how much actually traded" reporting
        # (get_total_volume, get_average_trade_size), independent of
        # how large the rolling window above is.
        self.total_volume = {symbol: 0 for symbol in self.symbols}
        self.total_trade_count = {symbol: 0 for symbol in self.symbols}
        self.total_notional = {symbol: 0.0 for symbol in self.symbols}

        # Symbol -> external fair value (drifts with noise + order
        # flow + regime, pulled back toward the long-run anchor)
        self.current_price = {
            symbol: starting_prices.get(symbol, 100)
            for symbol in self.symbols
        }

        # Symbol -> actual last executed trade price
        self.last_trade_price = {
            symbol: starting_prices.get(symbol, 100)
            for symbol in self.symbols
        }

        # Symbol -> slow-moving "true" long-run value that current_price
        # reverts toward.
        self.long_run_value = {
            symbol: starting_prices.get(symbol, 100)
            for symbol in self.symbols
        }

        self.impact_factor = impact_factor
        self.reversion_strength = reversion_strength
        self.anchor_volatility = anchor_volatility
        self.base_volatility = base_volatility

        # Symbol -> realized volatility estimate (exponentially
        # weighted), used for volatility clustering: a volatile step
        # makes the *next* step's noise draw larger too, rather than
        # every step being an independent, identically-sized shock.
        # This is what makes Problem #8 ("equity curves too smooth,
        # randomness should emerge naturally") actually emerge from
        # the price process itself instead of being bolted on
        # afterward.
        self._ewma_vol = {symbol: base_volatility for symbol in self.symbols}
        self._ewma_alpha = 0.06



    def _ensure_symbol(self, symbol):

        if symbol not in self.prices:

            self.symbols.append(symbol)
            self.prices[symbol] = []
            self.volumes[symbol] = []
            self.total_volume[symbol] = 0
            self.total_trade_count[symbol] = 0
            self.total_notional[symbol] = 0.0
            self.current_price[symbol] = 100
            self.last_trade_price[symbol] = 100
            self.long_run_value[symbol] = 100
            self._ewma_vol[symbol] = self.base_volatility



    def update_market_price(
        self,
        symbol="AAPL",
        order_flow_imbalance=0.0,
        regime_params=None
    ):
        """
        Simulates external market movement for a symbol.

        regime_params, if provided (see
        engine.market_regime.MarketRegimeEngine.step), is a dict with
        "drift", "vol_multiplier", and "reversion_multiplier" keys
        that reshape this step's process:

          - drift: a directional push added every step (positive ->
            trending up, negative -> trending down, 0 -> no
            persistent direction). This is what gives momentum
            strategies a real edge to detect during trending regimes
            -- something the original pure-OU process never had.
          - vol_multiplier: scales this step's random shock, letting
            "high_volatility"/"panic" regimes produce fat-tailed,
            bursty moves and "low_volatility" regimes produce calm
            ones.
          - reversion_multiplier: scales how hard price is pulled
            back to the long-run anchor. Low during trends (so the
            trend isn't fought), high during mean_reverting/
            low_volatility regimes (so range-bound behavior is
            genuine).
        """

        self._ensure_symbol(symbol)

        regime_params = regime_params or {
            "drift": 0.0,
            "vol_multiplier": 1.0,
            "reversion_multiplier": 1.0,
        }

        self.long_run_value[symbol] += random.gauss(
            0,
            self.anchor_volatility
        )

        if self.long_run_value[symbol] < 1:
            self.long_run_value[symbol] = 1

        # Volatility clustering: this step's shock size is drawn
        # using a blend of the base volatility and the recent
        # exponentially-weighted realized volatility, then the regime
        # multiplier is layered on top of that.
        effective_vol = (
            self._ewma_vol[symbol] * regime_params["vol_multiplier"]
        )

        noise = random.gauss(0, effective_vol)

        # Update the EWMA estimate using the magnitude of this step's
        # shock, so a burst of large moves keeps subsequent steps
        # elevated too (fat-tailed clustering) instead of every step
        # being independently sized.
        self._ewma_vol[symbol] = (
            (1 - self._ewma_alpha) * self._ewma_vol[symbol]
            + self._ewma_alpha * abs(noise)
        )

        drift = (
            order_flow_imbalance * self.impact_factor
            + regime_params["drift"]
        )

        reversion = (
            (self.long_run_value[symbol] - self.current_price[symbol])
            * self.reversion_strength
            * regime_params["reversion_multiplier"]
        )

        self.current_price[symbol] += noise + drift + reversion

        if self.current_price[symbol] < 1:
            self.current_price[symbol] = 1



    def record_trade(self, trade):

        symbol = trade.symbol

        self._ensure_symbol(symbol)

        self.prices[symbol].append(trade.price)
        self.volumes[symbol].append(trade.quantity)

        # Cumulative, unbounded accounting -- see module docstring.
        self.total_volume[symbol] += trade.quantity
        self.total_trade_count[symbol] += 1
        self.total_notional[symbol] += trade.price * trade.quantity

        self.last_trade_price[symbol] = trade.price

        self._trim_history_if_needed(symbol)



    def _trim_history_if_needed(self, symbol):

        if len(self.prices[symbol]) > 2 * PRICE_HISTORY_MAXLEN:

            self.prices[symbol] = self.prices[symbol][-PRICE_HISTORY_MAXLEN:]
            self.volumes[symbol] = self.volumes[symbol][-PRICE_HISTORY_MAXLEN:]



    def get_latest_price(self, symbol="AAPL"):

        self._ensure_symbol(symbol)

        return self.last_trade_price[symbol]



    def get_recent_prices(self, count, symbol="AAPL"):

        self._ensure_symbol(symbol)

        return self.prices[symbol][-count:]



    def get_fair_price(self, symbol="AAPL"):
        """
        Returns simulated external market value for a symbol -- the
        short-run process that wanders around the long-run anchor.
        """

        self._ensure_symbol(symbol)

        return self.current_price[symbol]



    def get_long_run_value(self, symbol="AAPL"):
        """
        Returns the slow-moving "true" fundamental value that
        get_fair_price() itself reverts toward.
        """

        self._ensure_symbol(symbol)

        return self.long_run_value[symbol]



    def get_recent_volatility(self, symbol="AAPL"):
        """
        Returns the current exponentially-weighted realized
        volatility estimate for a symbol. Useful for strategies that
        should widen thresholds/spreads in choppy conditions instead
        of using a fixed constant (see MarketMakerStrategy,
        ArbitrageStrategy, MeanReversionStrategy).
        """

        self._ensure_symbol(symbol)

        return self._ewma_vol[symbol]



    def get_total_volume(self, symbol=None):
        """
        Cumulative shares traded across the *entire* run. Fixed to
        read from the unbounded total_volume counters -- see module
        docstring for why this used to be wrong.
        """

        if symbol is not None:

            self._ensure_symbol(symbol)

            return self.total_volume[symbol]


        return sum(self.total_volume.values())



    def get_total_trade_count(self, symbol=None):

        if symbol is not None:

            self._ensure_symbol(symbol)

            return self.total_trade_count[symbol]

        return sum(self.total_trade_count.values())



    def get_average_trade_size(self, symbol=None):
        """
        Cumulative total volume / cumulative total trade count.
        Internally consistent with get_total_volume() and
        get_total_trade_count() by construction, since both are
        updated together in record_trade() -- this is the fix for
        Problem #2's "average trade size is effectively near zero".
        """

        count = self.get_total_trade_count(symbol)

        if count == 0:
            return 0.0

        return self.get_total_volume(symbol) / count



    def get_vwap(self, symbol="AAPL"):
        """
        Volume-weighted average price over the *entire* run
        (consistent with get_total_volume -- uses the same cumulative
        notional/volume counters, not the trimmed rolling window).
        """

        self._ensure_symbol(symbol)

        total_volume = self.total_volume[symbol]

        if total_volume == 0:
            return None

        return self.total_notional[symbol] / total_volume



    def get_recent_vwap(self, symbol="AAPL"):
        """
        VWAP over only the recent rolling window (bounded by
        PRICE_HISTORY_MAXLEN) -- useful for execution algorithms
        benchmarking against a recent VWAP rather than the full-run
        VWAP, e.g. WhaleStrategy.
        """

        self._ensure_symbol(symbol)

        prices = self.prices[symbol]
        volumes = self.volumes[symbol]

        if not prices:
            return None

        total_value = sum(
            price * volume for price, volume in zip(prices, volumes)
        )

        total_volume = sum(volumes)

        if total_volume == 0:
            return None

        return total_value / total_volume
