from engine.exchange import Exchange
from models.trader import Trader
from simulation.random_strategy import RandomStrategy
from simulation.market_simulator import MarketSimulator



def test_market_simulator_runs():

    exchange = Exchange()


    trader = Trader(
        trader_id=1,
        name="Bot",
        starting_cash=10000
    )


    exchange.register_trader(trader)


    strategy = RandomStrategy(trader)


    simulator = MarketSimulator(exchange)


    simulator.add_strategy(strategy)


    simulator.run_step()


    assert len(simulator.strategies) == 1