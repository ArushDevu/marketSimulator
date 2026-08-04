import matplotlib.pyplot as plt


# How many recent steps to keep drawing. Unbounded history makes the
# live window progressively slower to redraw as a run stretches into
# thousands of steps, so -- purely for the chart, not the underlying
# data -- we keep a rolling window.
MAX_PLOT_POINTS = 2000


CATEGORY_COLORS = {
    "noise": "gray",
    "momentum": "orange",
    "mean_reversion": "purple",
    "value": "teal",
    "market_maker": "red",
    "arbitrage": "gold",
    "institutional": "black",
    "random": "blue",
    "manual": "green",
}

SYMBOL_COLORS = [
    "blue", "green", "crimson", "darkorange", "purple", "teal", "black"
]

# Colors for individually-named tracked traders (e.g. the 8 benchmark
# traders in runner.py -- "Trader 1", "Whale", etc, or a manually
# added human/NullStrategy trader). These are drawn as bold, solid
# lines on TOP of the (lighter/dashed) category-aggregate lines, so a
# specific trader you care about doesn't get averaged away into its
# category's crowd.
NAMED_TRADER_COLORS = [
    "blue", "green", "orange", "red", "purple",
    "gray", "gold", "black", "crimson", "teal"
]


class LivePlot:
    """
    Live dashboard showing, per symbol, the traded price (with the
    active market regime annotated in the title -- see
    engine/market_regime.py), and, per trader *category* (not per
    individual trader), the mean return.
    """


    def __init__(self):

        plt.ion()

        self.fig, (self.price_ax, self.return_ax) = plt.subplots(
            2,
            1,
            figsize=(12, 8),
            sharex=True
        )

        self.steps = []

        # symbol -> list of prices, one per recorded step
        self.prices = {}


    def update(
        self,
        step,
        prices,
        category_return_history,
        trader_return_history=None,
        regime_label=None
    ):
        """
        prices: dict of {symbol: latest_price}, one entry per symbol
            the simulation is running.
        category_return_history: dict of {category: sequence of mean
            percentage returns, one per simulation step}. Drawn as
            light, dashed background lines -- the "crowd" view.
        trader_return_history: optional dict of {trader_name: sequence
            of percentage returns} -- only traders added with
            track_history=True. Drawn as bold, solid, individually
            labeled lines on top -- the "named trader" view. Omit or
            pass {} if you have no individually-tracked traders.
        regime_label: optional string, the currently active market
            regime (see MarketRegimeEngine.get_current_regime), shown
            in the price chart title as a lightweight stand-in for a
            full regime-timeline plot.
        """

        if not prices:
            return


        self.steps.append(step)

        for symbol, price in prices.items():

            if price is None:
                continue

            self.prices.setdefault(symbol, []).append(price)


        # Keep only the most recent window for redraw performance.
        if len(self.steps) > MAX_PLOT_POINTS:

            self.steps = self.steps[-MAX_PLOT_POINTS:]

            for symbol in self.prices:
                self.prices[symbol] = self.prices[symbol][-MAX_PLOT_POINTS:]


        #
        # Price chart -- every symbol, not just one hardcoded ticker
        #

        self.price_ax.clear()

        for i, (symbol, history) in enumerate(sorted(self.prices.items())):

            color = SYMBOL_COLORS[i % len(SYMBOL_COLORS)]

            # A series (symbol, category, or named trader) can have a
            # different number of recorded points than self.steps --
            # fewer if it started later, or more if it's drawing from
            # a longer-lived history than the plot's own step list has
            # kept. Clamp to the shorter of the two before slicing so
            # the x/y arrays passed to plot() always have matching
            # lengths (a naive `self.steps[-len(history):]` silently
            # returns fewer elements than requested when self.steps is
            # the shorter list, which caused a shape mismatch here).
            common_length = min(len(self.steps), len(history))

            aligned_steps = self.steps[-common_length:]
            aligned_history = history[-common_length:]

            self.price_ax.plot(
                aligned_steps,
                aligned_history,
                linewidth=2,
                label=symbol,
                color=color
            )


        title = "Live Stock Price"

        if regime_label is not None:
            title += f"   (regime: {regime_label})"

        self.price_ax.set_title(title)

        self.price_ax.set_ylabel(
            "Price"
        )

        self.price_ax.grid(True)
        self.price_ax.legend()


        #
        # Return chart -- category aggregates (light/dashed, the
        # "crowd") plus any individually-tracked named traders
        # (bold/solid, on top).
        #

        self.return_ax.clear()

        for category, history in sorted(category_return_history.items()):

            history_list = list(history)[-MAX_PLOT_POINTS:]

            if not history_list:
                continue

            # Align to real step numbers (matching self.steps, which
            # is what the price chart above uses) rather than plain
            # 0..len(history_list) index positions. The axes are
            # shared (sharex=True), so plotting against bare indices
            # made every return line appear to end wherever its own
            # trimmed history happened to run out, instead of at the
            # actual current step -- this is what caused the return
            # chart's lines to look truncated partway through the run
            # while the price chart above kept going. Clamped to the
            # shorter of the two lengths -- see price_ax loop above.
            common_length = min(len(self.steps), len(history_list))

            aligned_steps = self.steps[-common_length:]
            aligned_history = history_list[-common_length:]

            self.return_ax.plot(
                aligned_steps,
                aligned_history,
                label=f"{category} (avg)",
                color=CATEGORY_COLORS.get(category),
                linewidth=1,
                linestyle="--",
                alpha=0.4
            )


        if trader_return_history:

            for i, (name, history) in enumerate(
                sorted(trader_return_history.items())
            ):

                history_list = list(history)[-MAX_PLOT_POINTS:]

                if not history_list:
                    continue

                common_length = min(len(self.steps), len(history_list))

                aligned_steps = self.steps[-common_length:]
                aligned_history = history_list[-common_length:]

                color = NAMED_TRADER_COLORS[i % len(NAMED_TRADER_COLORS)]

                self.return_ax.plot(
                    aligned_steps,
                    aligned_history,
                    label=name,
                    color=color,
                    linewidth=2.2
                )


        self.return_ax.set_title(
            "Return: Named Traders (solid) vs. Category Averages (dashed)"
        )

        self.return_ax.set_xlabel(
            "Simulation Step"
        )

        self.return_ax.set_ylabel(
            "Return (%)"
        )

        self.return_ax.grid(True)

        self.return_ax.legend(
            loc="upper left"
        )


        plt.tight_layout()

        plt.pause(0.001)



    def show(self):

        plt.ioff()

        plt.show()
