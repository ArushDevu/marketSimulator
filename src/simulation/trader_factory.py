import random

from models.trader import Trader
from simulation.random_strategy import RandomStrategy
from simulation.strategies.momentum import MomentumStrategy
from simulation.strategies.mean_reversion import MeanReversionStrategy
from simulation.strategies.noise_trader import NoiseTraderStrategy
from simulation.strategies.market_maker import MarketMakerStrategy
from simulation.strategies.arbitrage import ArbitrageStrategy


# Strategy classes that just need (trader, symbol) to construct
_SIMPLE_STRATEGIES = [
    RandomStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    NoiseTraderStrategy,
    ArbitrageStrategy,
]


def spawn_crowd(
    exchange,
    simulator,
    count,
    symbol="AAPL",
    id_start=1000,
    starting_cash_range=(5000, 75000),
    starting_shares_range=(0, 150),
    market_maker_ratio=0.05
):
    """
    Creates `count` randomized traders, registers them with the
    exchange, assigns each a random strategy, and wires them into the
    simulator. Returns the list of (trader, strategy) pairs so the
    caller can inspect or tweak them further if needed.

    A small fraction (market_maker_ratio) are given the
    MarketMakerStrategy instead, since a market needs at least some
    liquidity providers to function -- an all-taker crowd would just
    starve the book.
    """

    created = []

    for i in range(count):

        trader_id = id_start + i

        starting_cash = random.uniform(*starting_cash_range)

        trader = Trader(
            trader_id=trader_id,
            name=f"Trader{trader_id}",
            starting_cash=starting_cash
        )

        starting_shares = random.randint(*starting_shares_range)

        if starting_shares > 0:
            trader.portfolio.add_position(symbol, starting_shares)

        exchange.register_trader(trader)

        if random.random() < market_maker_ratio:
            strategy = MarketMakerStrategy(trader, symbol=symbol)
        else:
            strategy_class = random.choice(_SIMPLE_STRATEGIES)
            strategy = strategy_class(trader, symbol=symbol)

        simulator.add_strategy(strategy)

        created.append((trader, strategy))

    return created
