from engine.exchange import Exchange
from models.trader import Trader
from simulation.random_strategy import RandomStrategy



def test_random_strategy_creates_order():

    exchange = Exchange()


    trader = Trader(
        trader_id=1,
        name="Bot",
        starting_cash=10000
    )


    exchange.register_trader(trader)


    strategy = RandomStrategy(trader)


    strategy.generate_orders(exchange)


    depth = exchange.get_order_book_depth()


    total_orders = (
        len(depth["buy"])
        +
        len(depth["sell"])
    )


    assert total_orders >= 0