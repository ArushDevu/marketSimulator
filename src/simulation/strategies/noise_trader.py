import random

from simulation.strategy import BaseStrategy


class NoiseTraderStrategy(BaseStrategy):
    """
    Liquidity-taking noise trader.

    Submits MARKET orders with fat-tailed (Pareto-distributed) sizes,
    mimicking the bursty, uninformed order flow you see in real
    markets: mostly small orders, with occasional large ones.

    Already used `return None` (not `[]`) for its no-attempt branches
    in the original version, so its activity accounting was correct
    from the start -- part of why it showed up as "always active"
    relative to strategies like arbitrage/mean-reversion/market-maker
    that returned `[]` for both "no signal" and "signal fired but
    order rested unfilled" (see arbitrage.py's docstring). Left
    functionally as-is; category-mix rebalancing (fewer purely
    uninformed noise traders relative to informed strategies) is
    handled in trader_factory.py instead of here.
    """

    category = "noise"

    def __init__(self, trader, symbol="AAPL", base_quantity=2, tail_alpha=2.5):

        super().__init__(trader, symbol)

        self.base_quantity = base_quantity

        # Lower alpha = fatter tail = more frequent big orders
        self.tail_alpha = tail_alpha


    def _fat_tailed_quantity(self):

        size = int(
            self.base_quantity * random.paretovariate(self.tail_alpha)
        )

        return max(1, min(size, 50))


    def generate_orders(
        self,
        exchange,
        market_data=None
    ):

        side = random.choice(["BUY", "SELL"])

        quantity = self._fat_tailed_quantity()


        if side == "BUY":

            estimate_price = (
                market_data.get_fair_price(self.symbol)
                if market_data is not None
                else None
            )

            if not estimate_price:
                estimate_price = 100


            max_quantity = int(
                self.trader.get_cash() // (estimate_price * 1.05)
            )

            if max_quantity <= 0:
                return None

            quantity = min(quantity, max_quantity)

            return self.trader.buy_market(
                self.symbol,
                quantity,
                exchange,
                market_data
            )


        else:

            shares = self.trader.get_position(self.symbol)

            if shares <= 0:
                return None

            quantity = min(quantity, shares)

            return self.trader.sell_market(
                self.symbol,
                quantity,
                exchange
            )
