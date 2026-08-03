from simulation.strategy import BaseStrategy


class MarketMakerStrategy(BaseStrategy):
    
    def generate_orders(self, exchange, market_data):
        current_price = market_data.get_fair_price(self.symbol)
        
        if current_price is None:
            current_price = 100

        shares = self.trader.get_position(self.symbol)
        cash = self.trader.get_cash()

        max_inventory = 200
        min_inventory = 50
        spread = 1

        if shares > max_inventory:
            buy_price = current_price - 3
            sell_price = current_price + 0.5
            
        elif shares < min_inventory:
            buy_price = current_price - 0.5
            sell_price = current_price + 3
            
        else:
            buy_price = current_price - spread / 2
            sell_price = current_price + spread / 2

        quantity = 5

        if shares < max_inventory and cash >= buy_price * quantity:
            self.trader.buy(symbol=self.symbol, quantity=quantity, price=buy_price, exchange=exchange)

        if shares > min_inventory:
            self.trader.sell(symbol=self.symbol, quantity=quantity, price=sell_price, exchange=exchange)