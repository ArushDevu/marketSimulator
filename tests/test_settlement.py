from models.order import Order
from models.trader import Trader
from engine.matching_engines import MatchingEngine



def test_trade_settlement_updates_portfolios():

    engine = MatchingEngine()


    # Create buyer and seller
    buyer = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )


    seller = Trader(
        trader_id=2,
        name="Bob",
        starting_cash=5000
    )


    # Seller already owns shares
    seller.portfolio.buy(
        "AAPL",
        10,
        100
    )


    # Register traders with exchange
    engine.register_trader(buyer)
    engine.register_trader(seller)



    # Seller places sell order
    sell_order = Order(
        order_id=1,
        trader_id=2,
        symbol="AAPL",
        side="SELL",
        order_type="LIMIT",
        price=150,
        quantity=5,
        timestamp=1
    )


    # Buyer places buy order
    buy_order = Order(
        order_id=2,
        trader_id=1,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=150,
        quantity=5,
        timestamp=2
    )


    engine.submit_order(sell_order)

    trades = engine.submit_order(buy_order)



    # Check trade happened
    assert len(trades) == 1
    assert trades[0].price == 150
    assert trades[0].quantity == 5



    # Buyer paid $750 and received 5 shares
    assert buyer.portfolio.cash == 9250
    assert buyer.portfolio.get_position("AAPL") == 5



    # Seller received $750 and lost 5 shares
    assert seller.portfolio.cash == 4750
    assert seller.portfolio.get_position("AAPL") == 5