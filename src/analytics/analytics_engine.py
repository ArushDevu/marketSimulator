from analytics.performance import PerformanceAnalyzer, DEFAULT_PERIODS_PER_YEAR


class AnalyticsEngine:
    """
    Produces a per-trader-category performance summary, combining
    PerformanceAnalyzer's risk/return metrics with trade-level
    statistics (count, average size, turnover, market share).

    Per-category returns (MarketSimulator.category_return_history) are
    a *mean percentage return across every trader in the category*,
    one data point per step -- there's no per-category equity_history
    the way there is for individually tracked traders. To still
    report Sharpe/Sortino/Calmar/drawdown at the category level, this
    builds a synthetic normalized equity curve by compounding the
    category's mean per-step returns starting from an index value of
    1.0.

    IMPORTANT CAVEAT: averaging across many traders each step
    (cross-sectional averaging) cancels out each trader's *individual*
    idiosyncratic noise by the law of large numbers, leaving a much
    smoother series than any single trader actually experiences. That
    smoothness inflates the resulting Sharpe/Sortino figures --
    sometimes dramatically, for large populations -- because Sharpe's
    denominator (volatility of the series being measured) collapses
    faster than its numerator (mean return) does. These category-level
    ratios should be read as "how consistent was this category's
    *average* outcome run-over-run", not as a claim about any
    individual trader's realized risk-adjusted return. For an
    individual trader's real Sharpe, use PerformanceAnalyzer directly
    on that trader's own equity_history (see runner.py's "benchmark
    traders" section, which does exactly that for the 8 named
    traders). This is a known limitation of the population-scale
    reporting approach, not a bug in the Sharpe calculation itself --
    documented rather than silently fixed, since fixing it properly
    would require retaining full per-trader return series for the
    entire population, which is the exact per-trader memory cost
    track_history=False exists to avoid for large crowds.
    """

    def __init__(self, performance_analyzer=None, periods_per_year=DEFAULT_PERIODS_PER_YEAR):

        self.performance = performance_analyzer or PerformanceAnalyzer()
        self.periods_per_year = periods_per_year


    def _synthetic_equity_curve(self, category_returns_pct):

        equity = [1.0]

        for pct in category_returns_pct:

            equity.append(equity[-1] * (1 + pct / 100))

        return equity


    def summarize_category(self, simulator, category):
        """
        Returns a dict of metrics for one category. Safe to call even
        for categories with little/no history (returns zeros/None
        rather than raising).
        """

        returns_pct = list(
            simulator.category_return_history.get(category, [])
        )

        returns_fraction = [r / 100 for r in returns_pct]

        equity_curve = self._synthetic_equity_curve(returns_pct)

        stats = simulator.category_trade_stats.get(
            category,
            {
                "volume_bought": 0, "volume_sold": 0,
                "trades_bought": 0, "trades_sold": 0,
                "notional_bought": 0.0, "notional_sold": 0.0,
            }
        )

        total_volume = stats["volume_bought"] + stats["volume_sold"]
        total_trades = stats["trades_bought"] + stats["trades_sold"]

        population = len(simulator.category_members.get(category, []))

        market_total_volume = simulator.market_data.get_total_volume()

        market_share = (
            (total_volume / market_total_volume) * 100
            if market_total_volume else 0.0
        )

        average_trade_size = (
            total_volume / total_trades if total_trades else 0.0
        )

        # Turnover: shares traded per member of the category -- a
        # population-independent measure of how actively each trader
        # in the category is trading, so a category with 3,000
        # members isn't automatically reported as "more active" than
        # one with 50 purely because it has more traders.
        turnover_per_trader = (
            total_volume / population if population else 0.0
        )

        activity_history = simulator.category_activity_history.get(
            category, []
        )

        steps_run = len(activity_history)

        active_steps = sum(1 for count in activity_history if count > 0)

        # Fill rate here means "fraction of simulation steps in which
        # at least one member of this category actually got a trade
        # filled" -- a proxy for execution quality given the data
        # actually available (there's no per-order fill/no-fill log
        # kept centrally). Documented as an approximation rather than
        # a precise fills/orders-submitted ratio.
        fill_rate = (active_steps / steps_run) if steps_run else 0.0

        return {
            "category": category,
            "population": population,
            "mean_return_pct": returns_pct[-1] if returns_pct else 0.0,
            "sharpe": self.performance.calculate_sharpe(
                returns_fraction, periods_per_year=self.periods_per_year
            ),
            "sortino": self.performance.calculate_sortino(
                returns_fraction, periods_per_year=self.periods_per_year
            ),
            "calmar": self.performance.calculate_calmar(
                equity_curve, periods_per_year=self.periods_per_year
            ),
            "max_drawdown_pct": self.performance.calculate_max_drawdown(
                equity_curve
            ),
            "profit_factor": self.performance.calculate_profit_factor(
                returns_fraction
            ),
            "win_rate": self.performance.calculate_win_rate(
                returns_fraction
            ),
            "trade_count": total_trades,
            "average_trade_size": round(average_trade_size, 2),
            "total_volume": total_volume,
            "turnover_per_trader": round(turnover_per_trader, 2),
            "market_share_pct": round(market_share, 2),
            "fill_rate": round(fill_rate, 3),
        }


    def summarize_all(self, simulator):
        """
        Returns {category: summary_dict} for every category the
        simulator has seen.
        """

        return {
            category: self.summarize_category(simulator, category)
            for category in simulator.category_members
        }


    def print_summary(self, simulator):

        summaries = self.summarize_all(simulator)

        print("\n" + "=" * 100)
        print("Category Performance Summary")
        print("(Sharpe/Sortino/Calmar use a cross-sectional mean return")
        print(" series -- see AnalyticsEngine's docstring: these measure")
        print(" consistency of the category's average outcome, not any")
        print(" one trader's individual risk-adjusted return.)")
        print("=" * 100)

        header = (
            f"{'Category':<15}{'Pop':>6}{'Return%':>10}{'Sharpe':>8}"
            f"{'Sortino':>9}{'Calmar':>9}{'MaxDD%':>8}{'WinRate':>9}"
            f"{'Trades':>9}{'AvgSize':>9}{'Turnover':>10}{'Mkt%':>7}"
        )

        print(header)

        for category, summary in sorted(summaries.items()):

            print(
                f"{category:<15}"
                f"{summary['population']:>6}"
                f"{summary['mean_return_pct']:>10.2f}"
                f"{summary['sharpe']:>8.2f}"
                f"{summary['sortino']:>9.2f}"
                f"{summary['calmar']:>9.2f}"
                f"{summary['max_drawdown_pct']:>8.2f}"
                f"{summary['win_rate']:>9.2%}"
                f"{summary['trade_count']:>9}"
                f"{summary['average_trade_size']:>9.2f}"
                f"{summary['turnover_per_trader']:>10.2f}"
                f"{summary['market_share_pct']:>7.1f}"
            )

        print("=" * 100)

        return summaries
