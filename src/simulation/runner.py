import sys
import os


CURRENT_DIR = os.path.dirname(__file__)

SRC_DIR = os.path.join(
    CURRENT_DIR,
    ".."
)

ROOT_DIR = os.path.join(
    CURRENT_DIR,
    "../.."
)


sys.path.append(SRC_DIR)
sys.path.append(ROOT_DIR)


from simulation.strategies.momentum import MomentumStrategy
from simulation.strategies.mean_reversion import MeanReversionStrategy
from simulation.strategies.noise_trader import NoiseTraderStrategy
from simulation.strategies.arbitrage import ArbitrageStrategy
from simulation.strategies.whale import WhaleStrategy
from engine.exchange import Exchange
from engine.commission_model import CommissionModel
from models.trader import Trader
from simulation.market_simulator import MarketSimulator
from simulation.random_strategy import RandomStrategy
from visualization.live_plot import LivePlot
from simulation.strategies.market_maker import MarketMakerStrategy
from simulation.trader_factory import spawn_crowd, DEFAULT_STRATEGY_MIX
from analytics.performance import PerformanceAnalyzer
from analytics.analytics_engine import AnalyticsEngine


SYMBOLS = ["AAPL", "GOOG"]

STARTING_PRICES = {
    "AAPL": 100,
    "GOOG": 150
}

# Commission charged on both sides of every trade, in basis points of
# notional. See engine/commission_model.py -- this is the central fix
# for Problem #7 (random traders outperforming professionals): with
# it in place, a strategy with no genuine edge drifts to a slightly
# negative expected return instead of zero/positive.
COMMISSION_BPS = 2.0

# ---------------------------------------------------------------------
# Population / run-length knobs.
# ---------------------------------------------------------------------
CROWD_SIZE = 3000
NUM_STEPS = 3000
HEALTH_CHECK_INTERVAL = 250
SHOW_LIVE_PLOT = True

# Fixed so a run can be reproduced exactly -- set to None for a fresh
# random regime path each run. Validating the changes in this file
# means running with a handful of different seeds and confirming the
# *distribution* of outcomes looks reasonable, not just one lucky
# path -- see the "multiple seeds" note at the bottom of main().
REGIME_SEED = None



def main():

    exchange = Exchange(
        commission_model=CommissionModel(commission_bps=COMMISSION_BPS)
    )


    #
    # A handful of named "benchmark" traders, individually tracked
    # (track_history=True is the MarketSimulator default) so their
    # PnL/Sharpe/drawdown gets printed at the end like before.
    #

    trader1 = Trader(trader_id=1, name="Trader 1", starting_cash=50000)
    trader2 = Trader(trader_id=2, name="Trader 2", starting_cash=50000)
    trader3 = Trader(trader_id=3, name="Momentum Trader", starting_cash=50000)
    trader4 = Trader(trader_id=4, name="Market Maker", starting_cash=100000)
    trader5 = Trader(trader_id=5, name="Mean Reversion Trader", starting_cash=50000)
    trader6 = Trader(trader_id=6, name="Noise Trader", starting_cash=50000)
    trader7 = Trader(trader_id=7, name="Arbitrageur", starting_cash=50000)
    trader8 = Trader(trader_id=8, name="Whale", starting_cash=200000)


    all_traders = [
        trader1, trader2, trader3, trader4,
        trader5, trader6, trader7, trader8
    ]


    starting_positions = {
        trader1: 100, trader2: 100, trader3: 100,
        trader4: 1000, trader5: 100, trader6: 100,
        trader7: 100, trader8: 100
    }

    for trader, quantity in starting_positions.items():

        trader.portfolio.add_position("AAPL", quantity)
        trader.portfolio.add_position("GOOG", quantity)


    for trader in all_traders:
        exchange.register_trader(trader)


    # AAPL strategies
    strategy1 = RandomStrategy(trader1, symbol="AAPL")
    strategy3 = MomentumStrategy(trader3, symbol="AAPL")
    strategy4 = MarketMakerStrategy(trader4, symbol="AAPL")
    strategy5 = MeanReversionStrategy(trader5, symbol="AAPL")
    strategy6 = NoiseTraderStrategy(trader6, symbol="AAPL")
    strategy7 = ArbitrageStrategy(trader7, symbol="AAPL")
    strategy8 = WhaleStrategy(
        trader8,
        symbol="AAPL",
        side="BUY",
        total_quantity=500
    )

    # GOOG strategy, to prove multi-symbol actually works
    strategy2 = RandomStrategy(trader2, symbol="GOOG")


    simulator = MarketSimulator(
        exchange,
        symbols=SYMBOLS,
        starting_prices=STARTING_PRICES,
        regime_seed=REGIME_SEED
    )


    for strategy in [
        strategy1, strategy2, strategy3, strategy4,
        strategy5, strategy6, strategy7, strategy8
    ]:
        simulator.add_strategy(strategy, track_history=True)


    #
    # The diverse crowd. Split across both symbols so GOOG actually
    # gets meaningful order flow too, not just Trader 2's random
    # orders. track_history=False for these, but they're still fully
    # counted in the per-category aggregates.
    #

    aapl_crowd_size = CROWD_SIZE // 2
    goog_crowd_size = CROWD_SIZE - aapl_crowd_size

    spawn_crowd(
        exchange,
        simulator,
        count=aapl_crowd_size,
        symbol="AAPL",
        id_start=10_000,
        strategy_mix=DEFAULT_STRATEGY_MIX
    )

    spawn_crowd(
        exchange,
        simulator,
        count=goog_crowd_size,
        symbol="GOOG",
        id_start=10_000 + aapl_crowd_size,
        strategy_mix=DEFAULT_STRATEGY_MIX
    )

    print(
        f"Spawned {aapl_crowd_size:,} AAPL agents and "
        f"{goog_crowd_size:,} GOOG agents "
        f"({CROWD_SIZE:,} total) alongside the 8 benchmark traders."
    )
    print("Population by category:")
    for category, members in sorted(simulator.category_members.items()):
        print(f"  {category:<15}{len(members):>7,}")


    plot = LivePlot() if SHOW_LIVE_PLOT else None


    for step in range(1, NUM_STEPS + 1):

        # Printing a line every single step floods the console once
        # you're running thousands of steps -- only do it sparingly.
        verbose = (step % HEALTH_CHECK_INTERVAL == 0)

        simulator.run_step(verbose=False)

        if plot is not None:

            latest_prices = {
                symbol: simulator.market_data.get_latest_price(symbol)
                for symbol in SYMBOLS
            }

            plot.update(
                step,
                latest_prices,
                simulator.category_return_history,
                trader_return_history=simulator.return_history,
                regime_label=simulator.regime_engine.get_current_regime(
                    SYMBOLS[0]
                )
            )

        if verbose:
            simulator.print_health_snapshot()


    print("\nSimulation complete")


    print(
        "Trades executed:",
        exchange.get_total_trades_executed()
    )


    print(
        "Total volume (all symbols):",
        simulator.market_data.get_total_volume()
    )

    print(
        "Average trade size (all symbols):",
        round(simulator.market_data.get_average_trade_size(), 3)
    )


    for symbol in SYMBOLS:

        print(
            f"VWAP ({symbol}):",
            simulator.market_data.get_vwap(symbol)
        )

        print(
            f"Final regime ({symbol}):",
            simulator.regime_engine.get_current_regime(symbol)
        )


    current_prices = {
        symbol: simulator.market_data.get_latest_price(symbol)
        for symbol in SYMBOLS
    }


    print("\nBenchmark Trader Performance")
    print("-" * 40)


    for trader in all_traders:

        print(trader.name)

        print("Cash:", round(trader.get_cash(), 2))

        for symbol in SYMBOLS:
            print(f"{symbol} Shares:", trader.get_position(symbol))

        print("Net Worth:", round(trader.get_net_worth(current_prices), 2))
        print("PnL:", round(trader.get_pnl(current_prices), 2))

        print()



    #
    # Performance Metrics (benchmark traders only -- these are the
    # ones with full per-step history tracked)
    #

    analyzer = PerformanceAnalyzer()


    print("\nPerformance Metrics (benchmark traders)")
    print("-" * 40)


    for trader in all_traders:

        history = simulator.equity_history[trader.name]

        returns = analyzer.calculate_returns(history)
        sharpe = analyzer.calculate_sharpe(returns)
        sortino = analyzer.calculate_sortino(returns)
        drawdown = analyzer.calculate_max_drawdown(history)

        print(trader.name)
        print("Sharpe (annualized):", round(sharpe, 3))
        print("Sortino (annualized):", round(sortino, 3))
        print("Max Drawdown:", round(drawdown, 3), "%")
        print()


    #
    # Category-level analytics -- see analytics/analytics_engine.py.
    # Covers the full population (not just the 8 tracked benchmark
    # traders), including Sharpe/Sortino/Calmar, trade count, average
    # trade size, turnover, and market share per category.
    #

    analytics_engine = AnalyticsEngine()

    analytics_engine.print_summary(simulator)


    #
    # Final aggregate health check across the entire population,
    # including the 3,000+ crowd agents.
    #

    print("\nFinal Population Health Check")
    simulator.print_health_snapshot()


    if plot is not None:
        # Keep graph open after simulation ends
        plot.show()



if __name__ == "__main__":
    main()
