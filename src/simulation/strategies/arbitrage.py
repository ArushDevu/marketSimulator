from simulation.strategy import BaseStrategy


class ArbitrageStrategy(BaseStrategy):
    """
    Trades toward the simulated "fair value" whenever the last traded
    price has drifted meaningfully away from it. Sizes its order using
    live book liquidity (estimate_market_fill) so it never asks for
    more than the book could realistically absorb.
    """

    def __init__(self, trader, symbol="AAPL", threshold=0.015, max_quantity=15):
        super().__init__(trader, symbol)
        self.threshold = threshold
        self.max_quantity = max_quantity
        
        
        

    def generate_orders(self, exchange, market_data):
        fair_price = market_data.get_fair_price(self.symbol)
        traded_price = market_data.get_latest_price(self.symbol)
        
        if not fair_price or not traded_price:
            return []

        deviation = (traded_price - fair_price) / fair_price

        if deviation < -self.threshold:
            avg_price, fillable = exchange.estimate_market_fill(self.symbol, "BUY", self.max_quantity)
            
            if not fillable:
                return []
            max_affordable = int(self.trader.get_cash() // (avg_price * 1.02))
            
            quantity = min(fillable, max_affordable, self.max_quantity)
            if quantity <= 0:
                return []
            
            return self.trader.buy(symbol=self.symbol, quantity=quantity, price=round(fair_price, 2), exchange=exchange)

        elif deviation > self.threshold:
            shares = self.trader.get_position(self.symbol)
            
            if shares <= 0:
                return []
            avg_price, fillable = exchange.estimate_market_fill(self.symbol, "SELL", self.max_quantity)
            quantity = min(shares, fillable, self.max_quantity)
            
            if quantity <= 0:
                return []
            return self.trader.sell(symbol=self.symbol, quantity=quantity, price=round(fair_price, 2), exchange=exchange)

        return []