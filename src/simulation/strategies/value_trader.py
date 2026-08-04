from simulation.strategy import BaseStrategy


class ValueStrategy(BaseStrategy):
    """
    Fundamental / "value investor" style trader.

    Unlike ArbitrageStrategy (which reacts to the *short-run* fair
    price -- the noisy process that jitters every step) or
    MeanReversionStrategy (which reacts to the *recent trade average*
    -- a purely technical signal), this strategy anchors on
    MarketData's slow-moving long-run fundamental value
    (get_long_run_value). That's a deliberately different, steadier
    signal: a real fundamental investor doesn't re-price their view of
    "what the company is worth" every tick, they trade when the
    traded price has drifted meaningfully away from their (slowly
    updating) estimate of intrinsic value, and they hold through
    short-term noise in between.

    Activity semantics fixed (None for "no attempt") -- see
    arbitrage.py's docstring for why this matters for the population
    health-check metrics.
    """

    category = "value"

    def __init__(self, trader, symbol="AAPL", threshold=0.03, max_quantity=10):

        super().__init__(trader, symbol)

        # Wider threshold than Arbitrage/MeanReversion -- fundamental
        # investors tolerate more short-term mispricing before acting.
        self.threshold = threshold
        self.max_quantity = max_quantity


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        intrinsic_value = market_data.get_long_run_value(self.symbol)
        traded_price = market_data.get_latest_price(self.symbol)

        if not intrinsic_value or not traded_price:
            return None


        deviation = (traded_price - intrinsic_value) / intrinsic_value


        # Trading below intrinsic value -> undervalued -> buy
        if deviation < -self.threshold:

            max_affordable = int(
                self.trader.get_cash() // traded_price
            )

            quantity = min(self.max_quantity, max_affordable)

            if quantity <= 0:
                return None

            return self.trader.buy(
                symbol=self.symbol,
                quantity=quantity,
                price=round(traded_price, 2),
                exchange=exchange
            )


        # Trading above intrinsic value -> overvalued -> sell
        elif deviation > self.threshold:

            shares = self.trader.get_position(self.symbol)

            if shares <= 0:
                return None

            quantity = min(self.max_quantity, shares)

            return self.trader.sell(
                symbol=self.symbol,
                quantity=quantity,
                price=round(traded_price, 2),
                exchange=exchange
            )


        return None
