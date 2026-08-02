from models.order import Order
from engine.order_book import OrderBook


def test_cancel_existing_order():

    book = OrderBook()

    order = Order(
        order_id=1,
        trader_id=101,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=150,
        quantity=10,
        timestamp=1
    )

    book.process_order(order)

    assert len(book.buy_levels) == 1
    assert order.order_id in book.orders

    result = book.cancel_order(1)

    assert result is True
    assert order.order_id not in book.orders
    assert len(book.buy_levels) == 0



def test_cancel_nonexistent_order():

    book = OrderBook()

    result = book.cancel_order(999)

    assert result is False