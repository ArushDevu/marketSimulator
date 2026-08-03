from simulation.strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    
    def __init__(self, trader, symbol="AAPL", lookback=10, threshold=0.01):
        super().__init__(trader, symbol)
        self.lookback = lookback
        self.threshold = threshold



    def generate_orders(self, exchange, market_data):
        prices = market_data.get_recent_prices(self.lookback, self.symbol)
        if len(prices) < self.lookback:
            return []

        average_price = sum(prices) / len(prices)
        
        latest_price = prices[-1]
        
        if average_price == 0:
            return []

        deviation = (latest_price - average_price) / average_price

        if deviation < -self.threshold:
            max_quantity = int(self.trader.get_cash() // latest_price)
            
            if max_quantity <= 0:
                return []
            
            quantity = min(5, max_quantity)
            
            return self.trader.buy(symbol=self.symbol, quantity=quantity, price=latest_price, exchange=exchange)
        
        elif deviation > self.threshold:
            shares = self.trader.get_position(self.symbol)
            
            if shares <= 0:
                return []
            quantity = min(5, shares)
            
            return self.trader.sell(symbol=self.symbol, quantity=quantity, price=latest_price, exchange=exchange)
        return []