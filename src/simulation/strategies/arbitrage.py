from simulation.strategy import BaseStrategy


class ArbitrageStrategy(BaseStrategy):
    """
    Trades toward the simulated external short-run "fair value"
    whenever the last traded price has drifted meaningfully away from
    it, capturing the mispricing the way a real (fast, statistical)
    arbitrageur would.

    Two changes from the original:

    1. Activity semantics fixed. Every "no trade" branch here used to
       `return []`, which is indistinguishable (under a truthiness
       check) from "submitted an order that just didn't fill" -- see
       market_maker.py's docstring for the full explanation. Genuine
       no-signal / no-attempt branches now `return None`; only an
       actual trader.buy()/trader.sell() call's result is returned
       directly.
    2. Threshold is no longer a fixed constant. A fixed absolute
       deviation threshold against a market whose typical deviation
       size changes over time (calm regime vs. volatile regime) means
       the strategy is either almost always inactive (threshold too
       wide for calm periods) or firing on noise (threshold too tight
       for volatile periods) -- exactly Problem #3's "arbitrage stays
       inactive for long periods" and Problem #11's "introduce
       adaptive behavior". The threshold now scales with recent
       realized volatility, so it naturally activates whenever
       today's mispricing is large *relative to* today's typical
       noise, in either regime.
    """

    category = "arbitrage"

    def __init__(
        self,
        trader,
        symbol="AAPL",
        base_threshold=0.006,
        volatility_scale=1.5,
        max_quantity=15
    ):

        super().__init__(trader, symbol)

        self.base_threshold = base_threshold
        self.volatility_scale = volatility_scale
        self.max_quantity = max_quantity


    def _current_threshold(self, market_data):

        fair_price = market_data.get_fair_price(self.symbol) or 1

        volatility = market_data.get_recent_volatility(self.symbol)

        # Volatility as a fraction of price, scaled up -- deviations
        # need to clear this before they're treated as a genuine
        # mispricing rather than noise.
        return self.base_threshold + (
            volatility / fair_price
        ) * self.volatility_scale


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        fair_price = market_data.get_fair_price(self.symbol)
        traded_price = market_data.get_latest_price(self.symbol)

        if not fair_price or not traded_price:
            return None


        threshold = self._current_threshold(market_data)

        deviation = (traded_price - fair_price) / fair_price


        if deviation < -threshold:

            avg_price, fillable = exchange.estimate_market_fill(
                self.symbol,
                "BUY",
                self.max_quantity
            )

            if not fillable:
                return None

            max_affordable = int(
                self.trader.get_cash() // (avg_price * 1.02)
            )

            quantity = min(fillable, max_affordable, self.max_quantity)

            if quantity <= 0:
                return None

            return self.trader.buy(
                symbol=self.symbol,
                quantity=quantity,
                price=round(fair_price, 2),
                exchange=exchange
            )


        elif deviation > threshold:

            shares = self.trader.get_position(self.symbol)

            if shares <= 0:
                return None

            avg_price, fillable = exchange.estimate_market_fill(
                self.symbol,
                "SELL",
                self.max_quantity
            )

            quantity = min(shares, fillable, self.max_quantity)

            if quantity <= 0:
                return None

            return self.trader.sell(
                symbol=self.symbol,
                quantity=quantity,
                price=round(fair_price, 2),
                exchange=exchange
            )


        return None
