from simulation.strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    Buys when price is trending upward, sells when trending downward.

    The original version compared only two points (prices[0] vs.
    prices[-1] over a 5-tick window) against a *purely mean-reverting*
    price process (see the original market_data.py). That combination
    guarantees momentum loses on average: the signal is noisy (two
    points, no confirmation), and even when it's right about the
    recent direction, the underlying process is engineered to snap
    back, so "buy after an uptick" walks straight into the reversion
    term. Problem #6 ("momentum always loses regardless of market
    conditions") isn't fixable by retuning this strategy alone --
    tightening or loosening it just changes *how fast* it loses,
    because the world it trades in never actually trends. The real
    fix is engine.market_regime.MarketRegimeEngine, which gives the
    market genuine trending_up/trending_down regimes for momentum to
    have an honest edge in.

    Given that the world can now trend, this version also earns that
    edge more legitimately:
      - A short vs. long moving-average crossover (trend
        confirmation) instead of a two-point comparison, so isolated
        noise ticks don't trigger a trade.
      - The crossover must clear a volatility-scaled threshold
        (confidence filter) -- a bigger, more decisive crossover is
        required in choppy conditions before acting, same idea as
        the adaptive thresholds in arbitrage.py / mean_reversion.py.
      - Activity semantics fixed (None for "no attempt", matching
        every other strategy -- see arbitrage.py's docstring).
    """

    category = "momentum"

    def __init__(
        self,
        trader,
        symbol="AAPL",
        short_window=5,
        long_window=20,
        base_confirmation=0.0015,
        volatility_scale=1.0
    ):

        super().__init__(trader, symbol)

        self.short_window = short_window
        self.long_window = long_window
        self.base_confirmation = base_confirmation
        self.volatility_scale = volatility_scale


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        prices = market_data.get_recent_prices(self.long_window, self.symbol)

        if len(prices) < self.long_window:
            return None

        short_avg = sum(prices[-self.short_window:]) / self.short_window
        long_avg = sum(prices) / len(prices)

        if long_avg == 0:
            return None

        crossover = (short_avg - long_avg) / long_avg

        volatility = market_data.get_recent_volatility(self.symbol)

        confirmation_needed = self.base_confirmation + (
            volatility / long_avg
        ) * self.volatility_scale

        latest_price = prices[-1]


        if crossover > confirmation_needed:

            max_quantity = int(
                self.trader.get_cash() // latest_price
            )

            if max_quantity <= 0:
                return None

            quantity = min(5, max_quantity)

            return self.trader.buy(
                symbol=self.symbol,
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        elif crossover < -confirmation_needed:

            shares = self.trader.get_position(self.symbol)

            if shares <= 0:
                return None

            quantity = min(5, shares)

            return self.trader.sell(
                symbol=self.symbol,
                quantity=quantity,
                price=latest_price,
                exchange=exchange
            )


        return None
