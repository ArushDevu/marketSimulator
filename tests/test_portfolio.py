from models.portfolio import Portfolio

def test_buy_stock():
    portfolio = Portfolio(10000)

    portfolio.buy(
        "AAPL",
        10,
        150
    )

    assert portfolio.cash == 8500
    assert portfolio.get_position("AAPL") == 10