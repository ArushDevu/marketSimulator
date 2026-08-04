from simulation.strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    Buys when the price has dropped meaningfully below its recent
    average (expecting it to bounce back up).
    Sells when the price has risen meaningfully above its recent
    average (expecting it to fall back down).

    See arbitrage.py's docstring for the two changes applied here too:
    activity semantics (None for "no attempt" vs. the actual
    trader.buy/sell result), and a volatility-scaled threshold instead
    of a fixed constant so the strategy naturally activates when
    today's move is large relative to today's typical noise, and
    stays quiet during genuinely calm/low-volatility regimes rather
    than firing on tiny, meaningless drifts.
    """

    category = "mean_reversion"

    def __init__(
        self,
        trader,
        symbol="AAPL",
        lookback=10,
        base_threshold=0.006,
        volatility_scale=1.2
    ):

        super().__init__(trader, symbol)

        self.lookback = lookback
        self.base_threshold = base_threshold
        self.volatility_scale = volatility_scale


    def _current_threshold(self, market_data, average_price):

        volatility = market_data.get_recent_volatility(self.symbol)

        if average_price <= 0:
            return self.base_threshold

        return self.base_threshold + (
            volatility / average_price
        ) * self.volatility_scale


    def generate_orders(
        self,
        exchange,
        market_data
    ):

        prices = market_data.get_recent_prices(self.lookback, self.symbol)

        if len(prices) < self.lookback:
            return None


        average_price = sum(prices) / len(prices)
        latest_price = prices[-1]

        if average_price == 0:
            return None

        deviation = (latest_price - average_price) / average_price

        threshold = self._current_threshold(market_data, average_price)


        if deviation < -threshold:

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


        elif deviation > threshold:

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
