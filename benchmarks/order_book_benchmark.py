import sys
import os
import time
import random


sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "src"
    )
)


from engine.order_book import OrderBook


def benchmark_sorted_list_order_book():

    print("=" * 50)
    print("Order Book SortedList Benchmark")
    print("=" * 50)

    order_book = OrderBook()
    price_levels = 100000

    print(f"\nAdding {price_levels:,} price levels...")

    start = time.perf_counter()

    for price in range(1, price_levels + 1):
        order_book.buy_levels[price] = None
        order_book.buy_prices.add(price)

    end = time.perf_counter()

    print("SortedList construction time:", round(end - start, 5), "seconds")

    print("\nTesting best bid lookup...")

    start = time.perf_counter()
    repetitions = 100000

    for _ in range(repetitions):
        order_book._get_best_bid_price()

    end = time.perf_counter()

    print(f"{repetitions:,} SortedList lookups:")
    print(round(end - start, 5), "seconds")


def benchmark_dictionary_scan():

    print("\n" + "=" * 50)
    print("Dictionary max() Benchmark")
    print("=" * 50)

    prices = {}
    price_levels = 100000

    print(f"\nAdding {price_levels:,} price levels...")

    for price in range(1, price_levels + 1):
        prices[price] = None

    print("\nTesting max(dictionary.keys())...")

    start = time.perf_counter()
    repetitions = 100000

    for _ in range(repetitions):
        max(prices.keys())

    end = time.perf_counter()

    print(f"{repetitions:,} dictionary scans:")
    print(round(end - start, 5), "seconds")


def benchmark_price_level_churn():

    print("\n" + "=" * 50)
    print("Price-Level Churn Benchmark (long-run memory behavior)")
    print("=" * 50)

    from models.order import Order

    order_book = OrderBook()

    cycles = 20000
    price = 100

    print(f"\nRunning {cycles:,} add/remove cycles at a single price level...")

    start = time.perf_counter()

    for i in range(cycles):

        order = Order(
            order_id=i, trader_id=1, symbol="AAPL", side="BUY",
            order_type="LIMIT", price=price, quantity=1, timestamp=i
        )

        order_book.process_order(order)
        order_book.cancel_order(i)

    end = time.perf_counter()

    print(round(end - start, 5), "seconds")
    print("Live buy price levels after churn (should be 0):", len(order_book.buy_prices))
    print("Orders still tracked (should be 0):", len(order_book.orders))


if __name__ == "__main__":

    benchmark_sorted_list_order_book()
    benchmark_dictionary_scan()
    benchmark_price_level_churn()
