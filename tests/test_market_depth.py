from engine.exchange import Exchange
from models.trader import Trader



def test_market_depth():

    exchange = Exchange()

    buyer = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )

    exchange.register_trader(buyer)


    buyer.buy(
        "AAPL",
        10,
        150,
        exchange
    )


    depth = exchange.get_order_book_depth()


    assert depth["buy"][150] == 10