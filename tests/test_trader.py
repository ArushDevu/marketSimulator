from models.trader import Trader


def test_create_trader():

    trader = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )


    assert trader.trader_id == 1
    assert trader.name == "Alice"
    assert trader.get_cash() == 10000



def test_trader_portfolio():

    trader = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )


    trader.portfolio.buy(
        "AAPL",
        10,
        100
    )


    assert trader.get_position("AAPL") == 10
    assert trader.get_cash() == 9000