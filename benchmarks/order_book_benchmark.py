import sys
import os
import time
import random


# Allow importing from src
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "src"
    )
)


from engine.order_book import OrderBook


def benchmark_heap_order_book():

    print("=" * 50)
    print("Order Book Heap Benchmark")
    print("=" * 50)


    order_book = OrderBook()


    # Create fake price levels
    price_levels = 100000


    print(f"\nAdding {price_levels:,} price levels...")


    start = time.perf_counter()


    for price in range(1, price_levels + 1):

        # Fake price levels directly
        order_book.buy_levels[price] = None

        # Store negative prices for max heap
        import heapq
        heapq.heappush(
            order_book.buy_heap,
            -price
        )


    end = time.perf_counter()


    print(
        "Heap construction time:",
        round(end - start, 5),
        "seconds"
    )



    # Benchmark best bid retrieval

    print("\nTesting best bid lookup...")


    start = time.perf_counter()


    repetitions = 100000


    for _ in range(repetitions):

        order_book._get_best_bid_price()


    end = time.perf_counter()


    print(
        f"{repetitions:,} heap lookups:"
    )

    print(
        round(end - start, 5),
        "seconds"
    )



def benchmark_dictionary_scan():

    print("\n" + "=" * 50)
    print("Dictionary max() Benchmark")
    print("=" * 50)


    prices = {}

    price_levels = 100000


    print(
        f"\nAdding {price_levels:,} price levels..."
    )


    for price in range(1, price_levels + 1):

        prices[price] = None



    print("\nTesting max(dictionary.keys())...")


    start = time.perf_counter()


    # Same number of lookups as heap benchmark
    repetitions = 100000


    for _ in range(repetitions):

        max(prices.keys())


    end = time.perf_counter()


    print(
        f"{repetitions:,} dictionary scans:"
    )


    print(
        round(end - start, 5),
        "seconds"
    )


if __name__ == "__main__":

    benchmark_heap_order_book()

    benchmark_dictionary_scan()