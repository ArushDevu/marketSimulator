class CommissionModel:
    """
    Applies a transaction cost to every settled trade.

    This is the fix for "random traders outperform professionals"
    (Problem #7) and part of the fix for "market makers earn
    unrealistically smooth profits" (Problem #5): in the original
    code, trading was completely free. A LIMIT order that never
    crosses the spread costs nothing to place, so a trader that
    happens to sit passively near the mid-price (which is what
    RandomStrategy does, by construction -- it prices around
    `current_price`) pays nothing and sometimes *earns* the spread by
    getting picked off by someone else's aggressive order. Meanwhile
    a strategy that always must fill immediately (MARKET orders, or a
    LIMIT crossed deliberately to guarantee execution -- see
    WhaleStrategy) pays the full spread on every single trade with no
    offsetting income. That asymmetry, not the traders' actual skill,
    is what was producing "random beats professional".

    A flat per-trade commission (charged to *both* sides, in basis
    points of notional) does two things:
      - Makes every strategy's expected return net of a real cost,
        so a strategy with no genuine edge (random entry/exit) drifts
        to a *slightly negative* expected return rather than zero or
        positive, which is what should happen once realistic frictions
        exist.
      - Gives market makers a genuine, quantifiable reason their
        quoted spread needs to exceed the commission just to break
        even, rather than earning "free" spread capture against a
        frictionless market.

    Configurable rather than hard-coded so callers can dial it to
    zero for tests, or split it into different maker/taker rates for
    more realistic microstructure experiments.
    """

    def __init__(self, commission_bps=2.0):
        """
        commission_bps: cost per trade, in basis points (1bps =
        0.01%) of trade notional, charged to *each* side of the
        trade independently (so a $100 trade at 2bps costs the buyer
        $0.02 and the seller $0.02, not $0.02 total).
        """

        if commission_bps < 0:
            raise ValueError("commission_bps cannot be negative")

        self.commission_bps = commission_bps


    def calculate_fee(self, price, quantity):
        """
        Returns the commission owed by one side of a trade.
        """

        notional = price * quantity

        return notional * (self.commission_bps / 10_000)
