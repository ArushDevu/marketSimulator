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


    for step in range(100):

        simulator.run_step()


        latest_price = simulator.market_data.get_latest_price()


        plot.update(
            step,
            latest_price
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


    # Keep graph open after simulation ends
    plot.show()



if __name__ == "__main__":
    main()