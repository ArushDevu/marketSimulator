from simulation.strategy import BaseStrategy


class WhaleStrategy(BaseStrategy):
    """
    Institutional-style trader working a large total position down
    into small slices over many steps (a simple TWAP), sizing each
    slice against visible liquidity so it doesn't blow through the
    book beyond its slippage tolerance.
    """

    def __init__(self, trader, symbol="AAPL", side="BUY", total_quantity=500,
                 slice_quantity=10, max_slippage=0.01):
        super().__init__(trader, symbol)
        self.side = side
        self.remaining_to_trade = total_quantity
        self.slice_quantity = slice_quantity
        self.max_slippage = max_slippage
        
        

    def generate_orders(self, exchange, market_data):
        if self.remaining_to_trade <= 0:
            return []

        fair_price = market_data.get_fair_price(self.symbol) or 100
        slice_size = min(self.slice_quantity, self.remaining_to_trade)

        avg_price, fillable = exchange.estimate_market_fill(self.symbol, self.side, slice_size)
        
        if not fillable:
            return []

        if fair_price > 0:
            slippage = abs(avg_price - fair_price) / fair_price
            
            if slippage > self.max_slippage:
                fillable = max(1, fillable // 2)

        quantity = min(slice_size, fillable)

        if self.side == "BUY":
            max_affordable = int(self.trader.get_cash() // (avg_price * 1.02))
            quantity = min(quantity, max_affordable)
            
            if quantity <= 0:
                return []
            
            result = self.trader.buy(symbol=self.symbol, quantity=quantity, price=round(avg_price * 1.005, 2), exchange=exchange)
        
        else:
            shares = self.trader.get_position(self.symbol)
            quantity = min(quantity, shares)
            
            if quantity <= 0:
                return []
            
            result = self.trader.sell(symbol=self.symbol, quantity=quantity, price=round(avg_price * 0.995, 2), exchange=exchange)

        self.remaining_to_trade -= quantity
        return result