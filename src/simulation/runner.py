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
from engine.exchange import Exchange
from models.trader import Trader
from simulation.market_simulator import MarketSimulator
from simulation.random_strategy import RandomStrategy
from visualization.live_plot import LivePlot
from simulation.strategies.market_maker import MarketMakerStrategy
from analytics.performance import PerformanceAnalyzer





def main():

    exchange = Exchange()


    trader1 = Trader(
        trader_id=1,
        name="Trader 1",
        starting_cash=50000
    )


    trader2 = Trader(
        trader_id=2,
        name="Trader 2",
        starting_cash=50000
    )
    
    
    trader3 = Trader(
        trader_id=3,
        name="Momentum Trader",
        starting_cash=50000
    )
    
    
    trader4 = Trader(
        trader_id=4,
        name="Market Maker",
        starting_cash=50000
    )


    # Give traders starting inventory
    # without spending their cash
    trader1.portfolio.add_position(
        "AAPL",
        100
    )

    trader2.portfolio.add_position(
        "AAPL",
        100
    )
    
    trader3.portfolio.add_position(
        "AAPL",
        100
    )
    
    trader4.portfolio.add_position(
        "AAPL",
        500
    )


    # Record each trader's starting net worth
    initial_prices = {
        "AAPL": 100
    }

    trader1.initialize_starting_value(initial_prices)
    trader2.initialize_starting_value(initial_prices)
    trader3.initialize_starting_value(initial_prices)
    trader4.initialize_starting_value(initial_prices)

    exchange.register_trader(trader1)
    exchange.register_trader(trader2)
    exchange.register_trader(trader3)
    exchange.register_trader(trader4)


    strategy1 = RandomStrategy(trader1)
    strategy2 = RandomStrategy(trader2)
    strategy3 = MomentumStrategy(trader3)
    strategy4 = MarketMakerStrategy(trader4)


    simulator = MarketSimulator(exchange)


    simulator.add_strategy(strategy1)
    simulator.add_strategy(strategy2)
    simulator.add_strategy(strategy3)
    simulator.add_strategy(strategy4)


    # Create live chart
    plot = LivePlot()


    for step in range(1000):

        simulator.run_step()


        latest_price = simulator.market_data.get_latest_price()


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
        "Total volume:",
        simulator.market_data.get_total_volume()
    )


    print(
        "VWAP:",
        simulator.market_data.get_vwap()
    )


    latest_price = simulator.market_data.get_latest_price()

    current_prices = {
        "AAPL": latest_price
    }


    print("\nTrader Performance")
    print("-" * 40)


    for trader in [
        trader1,
        trader2,
        trader3,
        trader4
    ]:

        print(trader.name)

        print(
            "Cash:",
            round(
                trader.get_cash(),
                2
            )
        )

        print(
            "Shares:",
            trader.get_position("AAPL")
        )

        print(
            "Net Worth:",
            round(
                trader.get_net_worth(current_prices),
                2
            )
        )

        print(
            "PnL:",
            round(
                trader.get_pnl(current_prices),
                2
            )
        )

        print()



    print("\nPnL History")

    for trader_name, history in simulator.pnl_history.items():
        print(
            trader_name,
            len(history),
        )


    #
    # Performance Metrics
    #

    analyzer = PerformanceAnalyzer()


    print("\nPerformance Metrics")
    print("-" * 40)


    for trader_name, history in simulator.equity_history.items():

        returns = analyzer.calculate_returns(
            history
        )

        sharpe = analyzer.calculate_sharpe(
            returns
        )

        drawdown = analyzer.calculate_max_drawdown(
            history
        )


        print(
            trader_name
        )

        print(
            "Sharpe:",
            round(
                sharpe,
                3
            )
        )

        print(
            "Max Drawdown:",
            round(
                drawdown,
                3
            ),
            "%"
        )

        print()





    # Keep graph open after simulation ends
    plot.show()



if __name__ == "__main__":
    main()