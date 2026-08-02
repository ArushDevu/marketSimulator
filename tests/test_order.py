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
    
def test_create_market_order():

    order = Order(
        order_id=4,
        trader_id=104,
        symbol="AAPL",
        side="BUY",
        order_type="MARKET",
        price=None,
        quantity=10,
        timestamp=4
    )

    assert order.order_type == "MARKET"
    assert order.price is None
    assert order.quantity == 10



def test_limit_order_requires_price():

    try:
        Order(
            order_id=5,
            trader_id=105,
            symbol="AAPL",
            side="BUY",
            order_type="LIMIT",
            price=None,
            quantity=10,
            timestamp=5
        )

        assert False

    except ValueError:
        assert True



def test_invalid_order_type():

    try:
        Order(
            order_id=6,
            trader_id=106,
            symbol="AAPL",
            side="BUY",
            order_type="INVALID",
            price=100,
            quantity=10,
            timestamp=6
        )

        assert False

    except ValueError:
        assert True