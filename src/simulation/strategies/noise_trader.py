import random
from simulation.strategy import BaseStrategy


class NoiseTraderStrategy(BaseStrategy):
    """
    Liquidity-taking noise trader. Submits MARKET orders with
    fat-tailed (Pareto-distributed) sizes -- mostly small orders,
    occasionally large ones, like real uninformed order flow.
    """

    def __init__(self, trader, symbol="AAPL", base_quantity=2, tail_alpha=2.5):
        super().__init__(trader, symbol)
        self.base_quantity = base_quantity
        self.tail_alpha = tail_alpha  # lower = fatter tail
        
        

    def _fat_tailed_quantity(self):
        size = int(self.base_quantity * random.paretovariate(self.tail_alpha))
        return max(1, min(size, 50))
    
    

    def generate_orders(self, exchange, market_data=None):
        side = random.choice(["BUY", "SELL"])
        quantity = self._fat_tailed_quantity()

        if side == "BUY":
            estimate_price = market_data.get_fair_price(self.symbol) if market_data is not None else None
            
            if not estimate_price:
                estimate_price = 100
                
            max_quantity = int(self.trader.get_cash() // (estimate_price * 1.05))
            
            if max_quantity <= 0:
                return None
            
            quantity = min(quantity, max_quantity)
            
            return self.trader.buy_market(self.symbol, quantity, exchange, market_data)
        
        else:
            shares = self.trader.get_position(self.symbol)
            
            if shares <= 0:
                return None
            
            quantity = min(quantity, shares)
            
            return self.trader.sell_market(self.symbol, quantity, exchange)