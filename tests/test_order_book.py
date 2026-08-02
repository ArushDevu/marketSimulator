from models.order import Order
from engine.order_book import OrderBook


def test_unmatched_buy_order_added():

    book = OrderBook()

    buy_order = Order(
        order_id=1,
        trader_id=101,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=100,
        quantity=10,
        timestamp=1
    )

    trades = book.process_order(buy_order)

    assert len(trades) == 0
    assert len(book.buy_levels) == 1
    assert book.buy_levels[100].orders[0] == buy_order



def test_buy_sell_match():

    book = OrderBook()

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

    book.process_order(sell_order)

    trades = book.process_order(buy_order)

    assert len(trades) == 1
    assert trades[0].quantity == 5
    assert trades[0].price == 100



def test_partial_fill():

    book = OrderBook()

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
        quantity=10,
        timestamp=2
    )

    book.process_order(sell_order)

    trades = book.process_order(buy_order)

    assert len(trades) == 1
    assert trades[0].quantity == 5

    assert len(book.buy_levels) == 1
    assert book.buy_levels[100].orders[0].remaining_quantity == 5



def test_no_price_match():

    book = OrderBook()

    sell_order = Order(
        order_id=1,
        trader_id=102,
        symbol="AAPL",
        side="SELL",
        order_type="LIMIT",
        price=101,
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

    book.process_order(sell_order)

    trades = book.process_order(buy_order)

    assert len(trades) == 0
    assert len(book.buy_levels) == 1
    assert len(book.sell_levels) == 1