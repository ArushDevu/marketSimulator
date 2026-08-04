import random

from models.trader import Trader
from simulation.strategies.momentum import MomentumStrategy
from simulation.strategies.mean_reversion import MeanReversionStrategy
from simulation.strategies.noise_trader import NoiseTraderStrategy
from simulation.strategies.market_maker import MarketMakerStrategy
from simulation.strategies.arbitrage import ArbitrageStrategy
from simulation.strategies.value_trader import ValueStrategy
from simulation.strategies.whale import WhaleStrategy


# Default population mix -- an approximation of a real market's
# participant composition.
#
# Rebalanced from the original mix (Problem #9: "evaluate whether
# this distribution produces believable market dynamics"). The
# original 35% noise / 10% market_maker / 5% institutional skew meant
# there was, proportionally, very little genuine liquidity provision
# relative to uninformed flow -- real equity markets have market
# makers and institutional participants providing a much larger share
# of resting liquidity than a 10%/5% slice suggests, and 35% pure
# noise is on the high side once noise traders are (as here) always
# liquidity-taking MARKET orders rather than a mix of informed/
# uninformed limit flow. Shifted weight from noise and momentum
# toward market_maker/institutional/arbitrage:
#
#   30% noise / retail-style traders      (was 35%)
#   15% momentum traders                  (was 20%)
#   15% mean-reversion traders            (unchanged)
#   10% value / fundamental traders       (unchanged)
#   15% market makers (liquidity providers) (was 10%)
#    7% arbitrage / statistical-arbitrage traders (was 5%)
#    8% institutional execution algos (TWAP/POV-style) (was 5%)
DEFAULT_STRATEGY_MIX = {
    "noise": 0.30,
    "momentum": 0.15,
    "mean_reversion": 0.15,
    "value": 0.10,
    "market_maker": 0.15,
    "arbitrage": 0.07,
    "institutional": 0.08,
}


def _build_strategy(category, trader, symbol):
    """
    Constructs one strategy instance for the given category. Per-
    instance parameters are randomized within a sensible range so
    traders in the same category aren't exact clones of each other
    (real noise traders don't all share one order size, real
    mean-reversion traders don't all share one lookback window, etc).
    """

    if category == "noise":

        return NoiseTraderStrategy(
            trader,
            symbol=symbol,
            base_quantity=random.randint(1, 4),
            tail_alpha=random.uniform(2.0, 3.5)
        )

    if category == "momentum":

        return MomentumStrategy(
            trader,
            symbol=symbol,
            short_window=random.randint(4, 8),
            long_window=random.randint(15, 30),
            base_confirmation=random.uniform(0.001, 0.003)
        )

    if category == "mean_reversion":

        return MeanReversionStrategy(
            trader,
            symbol=symbol,
            lookback=random.randint(5, 20),
            base_threshold=random.uniform(0.004, 0.01)
        )

    if category == "value":

        return ValueStrategy(
            trader,
            symbol=symbol,
            threshold=random.uniform(0.02, 0.06),
            max_quantity=random.randint(5, 15)
        )

    if category == "market_maker":

        return MarketMakerStrategy(
            trader,
            symbol=symbol,
            base_spread_bps=random.uniform(8, 25),
            max_inventory=random.randint(150, 300),
            base_quantity=random.randint(3, 8)
        )

    if category == "arbitrage":

        return ArbitrageStrategy(
            trader,
            symbol=symbol,
            base_threshold=random.uniform(0.003, 0.008),
            max_quantity=random.randint(10, 20)
        )

    if category == "institutional":

        return WhaleStrategy(
            trader,
            symbol=symbol,
            side=random.choice(["BUY", "SELL"]),
            total_quantity=random.randint(200, 800),
            max_participation_rate=random.uniform(0.08, 0.18)
        )

    raise ValueError(f"Unknown strategy category: {category}")



def _assign_categories(count, strategy_mix):
    """
    Turns a {category: proportion} mix into an exact list of `count`
    category labels. Uses rounding + a correction on the largest
    bucket (instead of independent random draws per trader) so the
    realized population matches the requested percentages closely
    even for smaller `count` values, then shuffles the order.
    """

    total_weight = sum(strategy_mix.values())

    if total_weight <= 0:
        raise ValueError("strategy_mix proportions must sum to > 0")

    counts = {
        category: int(round(count * weight / total_weight))
        for category, weight in strategy_mix.items()
    }

    diff = count - sum(counts.values())

    if diff != 0:
        largest_category = max(counts, key=counts.get)
        counts[largest_category] += diff

    labels = []

    for category in strategy_mix:
        labels.extend([category] * counts[category])

    random.shuffle(labels)

    return labels



def spawn_crowd(
    exchange,
    simulator,
    count,
    symbol="AAPL",
    id_start=1000,
    starting_cash_range=(5000, 75000),
    starting_shares_range=(0, 150),
    strategy_mix=None,
    track_history=False
):
    """
    Creates `count` randomized traders, registers them with the
    exchange, assigns each a strategy drawn from `strategy_mix`
    (defaults to DEFAULT_STRATEGY_MIX), and wires them into the
    simulator. Returns the list of (trader, strategy) pairs so the
    caller can inspect or tweak them further if needed.

    track_history controls whether every spawned trader gets a full
    per-step pnl/return/equity history (expensive for thousands of
    traders over thousands of steps -- see MarketSimulator). Defaults
    to False for a crowd; per-category aggregates are always tracked
    regardless, via simulator.category_return_history /
    get_health_snapshot().
    """

    strategy_mix = strategy_mix or DEFAULT_STRATEGY_MIX

    labels = _assign_categories(count, strategy_mix)

    created = []

    for i, category in enumerate(labels):

        trader_id = id_start + i

        starting_cash = random.uniform(*starting_cash_range)

        trader = Trader(
            trader_id=trader_id,
            name=f"{category}_{trader_id}",
            starting_cash=starting_cash,
            category=category
        )

        starting_shares = random.randint(*starting_shares_range)

        if starting_shares > 0:
            trader.portfolio.add_position(symbol, starting_shares)

        exchange.register_trader(trader)

        strategy = _build_strategy(category, trader, symbol)

        simulator.add_strategy(strategy, track_history=track_history)

        created.append((trader, strategy))

    return created
