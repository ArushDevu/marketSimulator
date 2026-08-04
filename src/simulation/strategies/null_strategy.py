from simulation.strategy import BaseStrategy


class NullStrategy(BaseStrategy):
    """
    A strategy that never generates its own orders.

    Used for human-controlled traders: they still need to be
    registered with the MarketSimulator (via add_strategy) so their
    PnL/equity history gets tracked each step, but their actual orders
    come from API calls, not from automatic per-step generation.

    Returns None (not the original `[]`) to correctly register as
    "no attempt" under the fixed activity-tracking semantics -- see
    arbitrage.py's docstring. Functionally identical either way
    (this strategy never submits real orders), but None is now the
    correct convention project-wide for "chose not to act".
    """

    category = "manual"

    def generate_orders(self, exchange, market_data=None):
        return None
