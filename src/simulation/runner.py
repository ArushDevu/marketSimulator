import sys
import os

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)


from engine.exchange import Exchange
from models.trader import Trader
from simulation.market_simulator import MarketSimulator
from simulation.random_strategy import RandomStrategy



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


    exchange.register_trader(trader1)
    exchange.register_trader(trader2)


    strategy1 = RandomStrategy(trader1)
    strategy2 = RandomStrategy(trader2)


    simulator = MarketSimulator(exchange)


    simulator.add_strategy(strategy1)
    simulator.add_strategy(strategy2)


    for step in range(100):

        simulator.run_step()


    print("Simulation complete")


    print(
        "Trades executed:",
        len(exchange.get_trade_history())
    )


    print(
        "Latest price:",
        simulator.market_data.get_latest_price()
    )



if __name__ == "__main__":
    main()