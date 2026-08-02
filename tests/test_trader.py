from models.trader import Trader
from engine.exchange import Exchange



def test_trader_buy_and_sell_orders():

    exchange = Exchange()


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


    # Give seller shares
    seller.portfolio.buy(
        "AAPL",
        10,
        100
    )


    # Register traders so settlement works
    exchange.matching_engine.register_trader(buyer)
    exchange.matching_engine.register_trader(seller)



    # Seller submits order
    seller.sell(
        symbol="AAPL",
        quantity=5,
        price=150,
        exchange=exchange
    )


    # Buyer submits matching order
    trades = buyer.buy(
        symbol="AAPL",
        quantity=5,
        price=150,
        exchange=exchange
    )


    # Trade happened
    assert len(trades) == 1
    assert trades[0].price == 150
    assert trades[0].quantity == 5


    # Portfolio updates
    assert buyer.get_position("AAPL") == 5
    assert buyer.get_cash() == 9250

    assert seller.get_position("AAPL") == 5
    assert seller.get_cash() == 4750