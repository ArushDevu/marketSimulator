from models.order import Order
from models.trade import Trade
import pytest

def test_create_trade():

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

    sell_order = Order(
        order_id=2,
        trader_id=102,
        symbol="AAPL",
        side="SELL",
        order_type="LIMIT",
        price=150,
        quantity=10,
        timestamp=2
    )

    trade = Trade(
        trade_id=1,
        buy_order=buy_order,
        sell_order=sell_order,
        price=150,
        quantity=5,
        timestamp=3
    )

    assert trade.symbol == "AAPL"
    assert trade.price == 150
    assert trade.quantity == 5
    
    
def test_trade_parties():

    buy_order = Order(
        1,101,"AAPL",
        "BUY",
        "LIMIT",
        150,
        10,
        1
    )

    sell_order = Order(
        2,102,"AAPL",
        "SELL",
        "LIMIT",
        150,
        10,
        2
    )

    trade = Trade(
        1,
        buy_order,
        sell_order,
        150,
        5,
        3
    )

    assert trade.get_buyer() == 101
    assert trade.get_seller() == 102