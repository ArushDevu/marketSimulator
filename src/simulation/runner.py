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
from models.trader import Trader
from simulation.market_simulator import MarketSimulator
from simulation.random_strategy import RandomStrategy
from visualization.live_plot import LivePlot
from simulation.strategies.market_maker import MarketMakerStrategy
from analytics.performance import PerformanceAnalyzer



SYMBOLS = ["AAPL", "GOOG"]

STARTING_PRICES = {
    "AAPL": 100,
    "GOOG": 150
}



def main():

    exchange = Exchange()


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


    # Give traders starting inventory in both symbols, without
    # spending their cash
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
        total_quantity=500,
        slice_quantity=10
    )

    # GOOG strategy, to prove multi-symbol actually works
    strategy2 = RandomStrategy(trader2, symbol="GOOG")


    simulator = MarketSimulator(
        exchange,
        symbols=SYMBOLS,
        starting_prices=STARTING_PRICES
    )


    for strategy in [
        strategy1, strategy2, strategy3, strategy4,
        strategy5, strategy6, strategy7, strategy8
    ]:
        simulator.add_strategy(strategy)


    # Create live chart
    plot = LivePlot()


    for step in range(1000):

        simulator.run_step()


        latest_price = simulator.market_data.get_latest_price("AAPL")


        plot.update(
            step,
            latest_price,
            simulator.return_history
        )


    print("Simulation complete")


    print(
        "Trades executed:",
        len(exchange.get_trade_history())
    )


    print(
        "Total volume (all symbols):",
        simulator.market_data.get_total_volume()
    )


    for symbol in SYMBOLS:

        print(
            f"VWAP ({symbol}):",
            simulator.market_data.get_vwap(symbol)
        )


    current_prices = {
        symbol: simulator.market_data.get_latest_price(symbol)
        for symbol in SYMBOLS
    }


    print("\nTrader Performance")
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
    # Performance Metrics
    #

    analyzer = PerformanceAnalyzer()


    print("\nPerformance Metrics")
    print("-" * 40)


    for trader_name, history in simulator.equity_history.items():

        returns = analyzer.calculate_returns(history)
        sharpe = analyzer.calculate_sharpe(returns)
        drawdown = analyzer.calculate_max_drawdown(history)

        print(trader_name)
        print("Sharpe:", round(sharpe, 3))
        print("Max Drawdown:", round(drawdown, 3), "%")
        print()



    # Keep graph open after simulation ends
    plot.show()



if __name__ == "__main__":
    main()
