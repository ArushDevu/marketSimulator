import random


class MarketData:
    """
    Stores historical market info per symbol, and simulates external
    price movement that reacts to order-book pressure (order flow
    imbalance) instead of being pure noise.

    The fair-value process is mean-reverting (Ornstein-Uhlenbeck
    style): order flow pushes it around, but it's continually pulled
    back toward a slow-moving long-run anchor. Without this, sustained
    one-sided order flow lets the fair price drift arbitrarily far
    from what's actually being traded -- unbounded and unrealistic.
    """

    def __init__(
        self,
        symbols=None,
        starting_prices=None,
        impact_factor=0.15,
        reversion_strength=0.03,
        anchor_volatility=0.05
    ):
        symbols = symbols or ["AAPL"]
        starting_prices = starting_prices or {}

        self.symbols = list(symbols)
        self.prices = {s: [] for s in self.symbols}
        self.volumes = {s: [] for s in self.symbols}
        self.current_price = {s: starting_prices.get(s, 100) for s in self.symbols}
        self.last_trade_price = {s: starting_prices.get(s, 100) for s in self.symbols}

        # Slow-moving "true" long-run value that current_price reverts
        # toward, so imbalance-driven drift can't run away unboundedly.
        
        self.long_run_value = {s: starting_prices.get(s, 100) for s in self.symbols}

        self.impact_factor = impact_factor
        self.reversion_strength = reversion_strength
        self.anchor_volatility = anchor_volatility



    def _ensure_symbol(self, symbol):
        
        if symbol not in self.prices:
            self.symbols.append(symbol)
            self.prices[symbol] = []
            self.volumes[symbol] = []
            self.current_price[symbol] = 100
            self.last_trade_price[symbol] = 100
            self.long_run_value[symbol] = 100



    def update_market_price(self, symbol="AAPL", order_flow_imbalance=0.0):
        self._ensure_symbol(symbol)

        self.long_run_value[symbol] += random.gauss(0, self.anchor_volatility)
        
        if self.long_run_value[symbol] < 1:
            self.long_run_value[symbol] = 1

        noise = random.gauss(0, 0.5)
        drift = order_flow_imbalance * self.impact_factor
        reversion = (self.long_run_value[symbol] - self.current_price[symbol]) * self.reversion_strength

        self.current_price[symbol] += noise + drift + reversion
        
        if self.current_price[symbol] < 1:
            self.current_price[symbol] = 1



    def record_trade(self, trade):
        
        symbol = trade.symbol
        
        self._ensure_symbol(symbol)
        
        self.prices[symbol].append(trade.price)
        
        self.volumes[symbol].append(trade.quantity)
        
        self.last_trade_price[symbol] = trade.price




    def get_latest_price(self, symbol="AAPL"):
        
        self._ensure_symbol(symbol)
        return self.last_trade_price[symbol]




    def get_recent_prices(self, count, symbol="AAPL"):
        
        self._ensure_symbol(symbol)
        return self.prices[symbol][-count:]




    def get_fair_price(self, symbol="AAPL"):
        
        self._ensure_symbol(symbol)
        return self.current_price[symbol]




    def get_total_volume(self, symbol=None):
        
        if symbol is not None:
            self._ensure_symbol(symbol)
            
            return sum(self.volumes[symbol])
        
        return sum(sum(v) for v in self.volumes.values())




    def get_vwap(self, symbol="AAPL"):
        
        self._ensure_symbol(symbol)
        prices = self.prices[symbol]
        volumes = self.volumes[symbol]
        
        if not prices:
            return None
        
        total_value = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)
        
        if total_volume == 0:
            return None
        
        return total_value / total_volume