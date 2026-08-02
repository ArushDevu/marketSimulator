from src.models.order import Order

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