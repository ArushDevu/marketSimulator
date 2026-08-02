from models.trader import Trader
from engine.matching_engines import MatchingEngine



def test_trader_buy_and_sell_orders():

    engine = MatchingEngine()


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


    # Give seller shares first
    seller.portfolio.buy(
        "AAPL",
        10,
        100
    )


    # Register traders so settlement works
    engine.register_trader(buyer)
    engine.register_trader(seller)



    # Seller submits order using Trader.sell()
    seller.sell(
        symbol="AAPL",
        quantity=5,
        price=150,
        engine=engine,
        timestamp=1
    )


    # Buyer submits order using Trader.buy()
    trades = buyer.buy(
        symbol="AAPL",
        quantity=5,
        price=150,
        engine=engine,
        timestamp=2
    )


    # Trade happened
    assert len(trades) == 1
    assert trades[0].price == 150
    assert trades[0].quantity == 5


    # Buyer received shares and paid
    assert buyer.get_position("AAPL") == 5
    assert buyer.get_cash() == 9250


    # Seller lost shares and received money
    assert seller.get_position("AAPL") == 5
    assert seller.get_cash() == 4750