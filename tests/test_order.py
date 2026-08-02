from models.order import Order
import pytest


def test_create_order():

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

    assert order.symbol == "AAPL"
    assert order.quantity == 10
    assert order.remaining_quantity == 10


def test_invalid_quantity():

    with pytest.raises(ValueError):

        Order(
            order_id=1,
            trader_id=101,
            symbol="AAPL",
            side="BUY",
            order_type="LIMIT",
            price=150,
            quantity=0,
            timestamp=1
        )


def test_order_fill():

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

    order.fill(4)

    assert order.remaining_quantity == 6
    assert order.is_filled() == False