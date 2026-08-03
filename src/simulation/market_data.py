import random


class MarketData:
    """
    Stores historical market information per symbol, and simulates
    external price movement that reacts to real order-book pressure
    (order flow imbalance) instead of being pure noise.

    The fair-value process is mean-reverting (Ornstein-Uhlenbeck
    style): order flow pushes it around, but it's continually pulled
    back toward a slow-moving long-run anchor. Without this, sustained
    one-sided order flow (which is common with a small, biased
    population of trading strategies) would let the fair price drift
    arbitrarily far from what's actually being traded -- unbounded and
    unrealistic. With it, a steady imbalance settles into a bounded
    equilibrium offset instead of running away forever.
    """


    def __init__(
        self,
        symbols=None,
        starting_prices=None,
        impact_factor=0.15,
        reversion_strength=0.03,
        anchor_volatility=0.05
    ):

        symbols = symbols or ["AAPL"]
        starting_prices = starting_prices or {}

        self.symbols = list(symbols)

        # Symbol -> list of executed trade prices / volumes
        self.prices = {symbol: [] for symbol in self.symbols}
        self.volumes = {symbol: [] for symbol in self.symbols}

        # Symbol -> external fair value (drifts with noise + order flow,
        # pulled back toward the long-run anchor)
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
        # reverts toward. This itself wanders very slowly, so the market
        # can have real long-run trends without the imbalance-driven
        # drift being able to run away unboundedly in the short run.
        self.long_run_value = {
            symbol: starting_prices.get(symbol, 100)
            for symbol in self.symbols
        }

        # How strongly order-flow imbalance pushes the fair price
        self.impact_factor = impact_factor

        # How strongly the fair price is pulled back toward the anchor
        self.reversion_strength = reversion_strength

        # Volatility of the long-run anchor's own slow drift
        self.anchor_volatility = anchor_volatility



    def _ensure_symbol(self, symbol):
        """
        Lazily registers a symbol the first time it's referenced, so
        callers don't have to pre-declare every symbol up front.
        """

        if symbol not in self.prices:

            self.symbols.append(symbol)
            self.prices[symbol] = []
            self.volumes[symbol] = []
            self.current_price[symbol] = 100
            self.last_trade_price[symbol] = 100
            self.long_run_value[symbol] = 100



    def update_market_price(self, symbol="AAPL", order_flow_imbalance=0.0):
        """
        Simulates external market movement for a symbol.

        order_flow_imbalance should be in [-1, 1]: positive means more
        resting buy interest than sell interest (price should drift
        up), negative means the opposite.
        """

        self._ensure_symbol(symbol)


        # The long-run anchor wanders very slowly on its own -- this is
        # what lets the market have genuine long-run trends.
        self.long_run_value[symbol] += random.gauss(
            0,
            self.anchor_volatility
        )

        if self.long_run_value[symbol] < 1:
            self.long_run_value[symbol] = 1


        noise = random.gauss(
            0,
            0.5
        )

        drift = order_flow_imbalance * self.impact_factor

        # Pulls current_price back toward the anchor, proportional to
        # how far it has strayed -- this is what bounds the drift.
        reversion = (
            (self.long_run_value[symbol] - self.current_price[symbol])
            * self.reversion_strength
        )

        self.current_price[symbol] += noise + drift + reversion


        # Prevent unrealistic prices
        if self.current_price[symbol] < 1:
            self.current_price[symbol] = 1



    def record_trade(self, trade):
        """
        Records a completed trade under its own symbol.
        """

        symbol = trade.symbol

        self._ensure_symbol(symbol)


        self.prices[symbol].append(
            trade.price
        )

        self.volumes[symbol].append(
            trade.quantity
        )

        # Actual market price follows executed trades
        self.last_trade_price[symbol] = trade.price



    def get_latest_price(self, symbol="AAPL"):
        """
        Returns last executed trade price for a symbol.
        """

        self._ensure_symbol(symbol)

        return self.last_trade_price[symbol]



    def get_recent_prices(self, count, symbol="AAPL"):
        """
        Returns the last N executed prices for a symbol.
        """

        self._ensure_symbol(symbol)

        return self.prices[symbol][-count:]



    def get_fair_price(self, symbol="AAPL"):
        """
        Returns simulated external market value for a symbol.
        """

        self._ensure_symbol(symbol)

        return self.current_price[symbol]


    def get_total_volume(self, symbol=None):
        """
        Returns total traded volume, either for one symbol or,
        if no symbol is given, summed across every symbol.
        """

        if symbol is not None:

            self._ensure_symbol(symbol)

            return sum(self.volumes[symbol])


        return sum(
            sum(volumes)
            for volumes in self.volumes.values()
        )



    def get_vwap(self, symbol="AAPL"):
        """
        Returns volume weighted average price for a symbol.
        """

        self._ensure_symbol(symbol)

        prices = self.prices[symbol]
        volumes = self.volumes[symbol]

        if not prices:
            return None


        total_value = sum(
            price * volume
            for price, volume in zip(
                prices,
                volumes
            )
        )


        total_volume = sum(
            volumes
        )

        if total_volume == 0:
            return None


        return total_value / total_volume
