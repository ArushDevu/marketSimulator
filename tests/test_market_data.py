from engine.exchange import Exchange
from models.trader import Trader


def test_exchange_best_bid_and_ask():

    exchange = Exchange()

    buyer = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )

    seller = Trader(
        trader_id=2,
        name="Bob",
        starting_cash=10000
    )


    exchange.register_trader(buyer)
    exchange.register_trader(seller)


    seller.sell(
        "AAPL",
        10,
        150,
        exchange
    )

    buyer.buy(
        "AAPL",
        10,
        140,
        exchange
    )


    assert exchange.get_best_bid().price == 140
    assert exchange.get_best_ask().price == 150