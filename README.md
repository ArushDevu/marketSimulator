# Market Simulator

A simulated exchange and market microstructure research platform.

## Current Features

## Planned Features

An order is:
- BUY or SELL
- a quantity
- a price

A BUY order means:
"I am willing to pay up to this price."

A SELL order means:
"I am willing to accept at least this price."

A trade can happen when:
highest BUY price >= lowest SELL price.

BUY $100, SELL $99 → trade
BUY $98, SELL $99 → no trade
BUY 100 units, SELL 40 units → 40 trade, 60 remain
BUY 40 units, SELL 100 units → 40 trade, seller has 60 remain
BUY $100, SELL $100 → trade