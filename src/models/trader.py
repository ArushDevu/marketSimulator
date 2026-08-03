from models.portfolio import Portfolio
from models.order import Order


class Trader:
    def __init__(self, trader_id, name, starting_cash):
        self.trader_id = trader_id
        self.name = name
        self.portfolio = Portfolio(starting_cash)
        self.starting_value = None

    def get_cash(self):
        return self.portfolio.cash

    def get_position(self, symbol):
        return self.portfolio.get_position(symbol)

    def initialize_starting_value(self, prices):
        self.starting_value = self.portfolio.get_total_value(prices)

    def get_net_worth(self, prices):
        return self.portfolio.get_total_value(prices)

    def get_pnl(self, prices):
        if self.starting_value is None:
            raise ValueError("Starting value has not been initialized.")
        
        return self.get_net_worth(prices) - self.starting_value


    def buy(self, symbol, quantity, price, exchange):
        
        
        """Creates and submits a LIMIT BUY order through the exchange."""
        
        
        cost = quantity * price
        
        
        if not self.portfolio.reserve_cash(cost):
            return None
        current_step = exchange.get_timestamp()
        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100
        )
        
        return exchange.matching_engine.submit_order(order)



    def sell(self, symbol, quantity, price, exchange):
        
        """Creates and submits a LIMIT SELL order through the exchange."""
        
        if not self.portfolio.reserve_shares(symbol, quantity):
            return None
        current_step = exchange.get_timestamp()
        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="LIMIT",
            price=price,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100
        )
        return exchange.matching_engine.submit_order(order)



    def buy_market(self, symbol, quantity, exchange, market_data=None):
        """
        Creates and submits a MARKET BUY order. Since a market order has
        no set price, we estimate the likely execution cost by walking
        the live order book first (falling back to simulated fair value
        if the book is empty), then reserve 2% extra to cover the price
        moving against us while the order is in flight.
        """
        estimated_price, _ = exchange.estimate_market_fill(symbol, "BUY", quantity)

        if estimated_price is None:
            estimated_price = (
                market_data.get_fair_price(symbol) if market_data is not None else None
            )

        if not estimated_price:
            estimated_price = 100

        reservation_price = estimated_price * 1.02
        
        cost = quantity * reservation_price

        if not self.portfolio.reserve_cash(cost):
            return None

        current_step = exchange.get_timestamp()
        
        
        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="BUY",
            order_type="MARKET",
            price=None,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100,
            reservation_price=reservation_price
        )
        
        
        return exchange.matching_engine.submit_order(order)



    def sell_market(self, symbol, quantity, exchange):
        
        
        """Creates and submits a MARKET SELL order."""
        
        
        if not self.portfolio.reserve_shares(symbol, quantity):
            return None
        
        
        current_step = exchange.get_timestamp()
        
        
        order = Order(
            order_id=exchange.get_next_order_id(),
            trader_id=self.trader_id,
            symbol=symbol,
            side="SELL",
            order_type="MARKET",
            price=None,
            quantity=quantity,
            timestamp=current_step,
            expiry_step=current_step + 100
        )
        
        
        return exchange.matching_engine.submit_order(order)