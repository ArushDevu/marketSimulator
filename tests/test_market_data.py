from engine.exchange import Exchange
from models.trader import Trader
from models.order import Order
from models.trade import Trade
from simulation.market_data import MarketData



def test_exchange_best_bid_and_ask():

    exchange = Exchange()

    buyer = Trader(
        trader_id=1,
        name="Alice",
        starting_cash=10000
    )

    seller = Trader(
        trader_id=2,
        name="Bob",
        starting_cash=10000
    )


    exchange.register_trader(buyer)
    exchange.register_trader(seller)


    seller.sell(
        "AAPL",
        10,
        150,
        exchange
    )

    buyer.buy(
        "AAPL",
        10,
        140,
        exchange
    )


    assert exchange.get_best_bid().price == 140
    assert exchange.get_best_ask().price == 150





def test_market_data_records_trade():

    data = MarketData()


    buy_order = Order(
        order_id=1,
        trader_id=1,
        symbol="AAPL",
        side="BUY",
        order_type="LIMIT",
        price=150,
        quantity=10,
        timestamp=1
    )


    sell_order = Order(
        order_id=2,
        trader_id=2,
        symbol="AAPL",
        side="SELL",
        order_type="LIMIT",
        price=150,
        quantity=10,
        timestamp=1
    )


    trade = Trade(
        trade_id=1,
        buy_order=buy_order,
        sell_order=sell_order,
        price=150,
        quantity=10,
        timestamp=1
    )


    data.record_trade(trade)


    assert data.get_latest_price() == 150
    assert data.volumes[0] == 10