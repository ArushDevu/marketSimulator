from engine.exchange import Exchange


def test_exchange_generates_order_ids():

    exchange = Exchange()

    assert exchange.get_next_order_id() == 1
    assert exchange.get_next_order_id() == 2



def test_exchange_generates_timestamps():

    exchange = Exchange()

    assert exchange.get_timestamp() == 1
    assert exchange.get_timestamp() == 2