from models.order import Order
from engine.price_level import PriceLevel


def test_add_order_to_price_level():

    level = PriceLevel(150)

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

    level.add_order(order)

    assert len(level.orders) == 1
    assert level.orders[0] == order



def test_remove_order_from_price_level():

    level = PriceLevel(150)

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

    level.add_order(order)

    level.remove_order(order)

    assert len(level.orders) == 0



def test_price_level_volume():

    level = PriceLevel(150)

    order1 = Order(
        1,
        101,
        "AAPL",
        "BUY",
        "LIMIT",
        150,
        10,
        1
    )

    order2 = Order(
        2,
        102,
        "AAPL",
        "BUY",
        "LIMIT",
        150,
        20,
        2
    )

    level.add_order(order1)
    level.add_order(order2)

    assert level.get_volume() == 30



def test_get_first_order():

    level = PriceLevel(150)

    first_order = Order(
        1,
        101,
        "AAPL",
        "BUY",
        "LIMIT",
        150,
        10,
        1
    )

    second_order = Order(
        2,
        102,
        "AAPL",
        "BUY",
        "LIMIT",
        150,
        20,
        2
    )

    level.add_order(first_order)
    level.add_order(second_order)

    assert level.get_first_order() == first_order   