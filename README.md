## Order Book Performance Benchmark

The order book uses heap-based priority queues to efficiently retrieve the best bid and ask prices.

Benchmark configuration:

- Price levels: 100,000
- Lookups tested: 100,000

| Method | Time |
|---|---:|
| Heap priority queue | 0.00919 seconds |
| Dictionary max() scan | 78.83785 seconds |

Speed improvement:

~8,500x faster

### Complexity

| Operation | Old approach | Heap approach |
|---|---|---|
| Best bid retrieval | O(n) | O(1) |
| Best ask retrieval | O(n) | O(1) |

The heap implementation uses:
- Max heap for buy prices
- Min heap for sell prices
- Lazy deletion for stale price levels