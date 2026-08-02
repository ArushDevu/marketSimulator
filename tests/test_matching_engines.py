from models.order import Order
from engine.matching_engines import MatchingEngine


def test_engine_records_trade():

    engine = MatchingEngine()

    sell_order = Order(
        order_id=1,
        trader_id=102,
        symbol="AAPL",
        side="SELL",
        order_type="LIMIT",
        price=100,
        quantity=5,
        timestamp=1
    )

    buy_order = Order(
        order_id=2,
        trader_id=101,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=100,
        quantity=5,
        timestamp=2
    )

    engine.submit_order(sell_order)

    trades = engine.submit_order(buy_order)

    assert len(trades) == 1
    assert len(engine.get_trade_history()) == 1
    assert trades[0].quantity == 5



def test_engine_best_bid():

    engine = MatchingEngine()

    buy_order = Order(
        order_id=1,
        trader_id=101,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=150,
        quantity=10,
        timestamp=1
    )

    engine.submit_order(buy_order)

    best_bid = engine.get_best_bid()

    assert best_bid.price == 150