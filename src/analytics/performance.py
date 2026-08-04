import math


# Default annualization factor: treats one simulation step as one
# trading period within a 252-trading-day year. This is a modeling
# choice, not a law of nature -- callers running a simulation where a
# "step" represents something else (an intraday tick, an hour, etc.)
# should pass their own periods_per_year. It's exposed as a parameter
# rather than hard-coded specifically so it's not silently wrong for
# a different step definition.
DEFAULT_PERIODS_PER_YEAR = 252


class PerformanceAnalyzer:
    """
    Calculates trading performance metrics.

    Problem #10 ("Sharpe ratios for nearly every strategy are close
    to zero") traced to a genuine bug, not just a missing feature:
    calculate_sharpe() returned mean_return / volatility computed
    directly on *per-step* returns, with no annualization at all. A
    per-step Sharpe and an annualized Sharpe measure the same
    underlying skill, but standard practice (and every Sharpe ratio
    a reader would recognize as "normal", e.g. 0.5-3) is the
    annualized figure -- the per-step figure is smaller by a factor
    of sqrt(periods_per_year) purely from the unit convention, which
    for a 3,000-step run is a ~50x understatement. That's precisely
    why the reported numbers clustered near zero even where a real,
    consistent edge existed in the underlying returns. Fixed by
    annualizing: multiply the per-step Sharpe by sqrt(periods_per_year).

    Also added: Sortino (penalizes only downside deviation, so a
    strategy with lumpy-but-rare losses isn't penalized for its
    upside volatility the way Sharpe does), Calmar (return relative
    to max drawdown -- rewards strategies that don't blow up even if
    their Sharpe is only middling), profit factor, and win rate.
    """

    def calculate_returns(self, equity_history):

        returns = []

        for i in range(1, len(equity_history)):

            previous = equity_history[i-1]
            current = equity_history[i]

            if previous == 0:
                continue

            change = (
                (current - previous)
                /
                previous
            )

            returns.append(
                change
            )

        return returns



    def calculate_sharpe(
        self,
        returns,
        periods_per_year=DEFAULT_PERIODS_PER_YEAR,
        risk_free_rate_per_period=0.0
    ):
        """
        Annualized Sharpe ratio. risk_free_rate_per_period is
        expressed in the same units as `returns` (per-step, e.g.
        0.0001 for a step-level risk-free rate) -- defaults to 0,
        appropriate for a short-run simulation where treating the
        risk-free rate as negligible relative to trading returns is
        a reasonable simplification, but exposed for callers who want
        a real benchmark subtracted.
        """

        if len(returns) < 2:
            return 0

        excess_returns = [r - risk_free_rate_per_period for r in returns]

        mean_return = sum(excess_returns) / len(excess_returns)

        variance = sum(
            (r - mean_return) ** 2
            for r in excess_returns
        ) / (len(excess_returns) - 1)

        volatility = math.sqrt(variance)

        if volatility == 0:
            return 0

        per_period_sharpe = mean_return / volatility

        return per_period_sharpe * math.sqrt(periods_per_year)



    def calculate_sortino(
        self,
        returns,
        periods_per_year=DEFAULT_PERIODS_PER_YEAR,
        risk_free_rate_per_period=0.0
    ):
        """
        Like Sharpe, but only penalizes downside volatility (returns
        below the risk-free/target rate). A strategy that has large
        upside swings but small, controlled downside should score
        better here than under Sharpe, which treats both directions
        of volatility as equally "risky".
        """

        if len(returns) < 2:
            return 0

        excess_returns = [r - risk_free_rate_per_period for r in returns]

        mean_return = sum(excess_returns) / len(excess_returns)

        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return 0

        downside_variance = sum(r ** 2 for r in downside_returns) / len(
            excess_returns
        )

        downside_deviation = math.sqrt(downside_variance)

        if downside_deviation == 0:
            return 0

        per_period_sortino = mean_return / downside_deviation

        return per_period_sortino * math.sqrt(periods_per_year)



    def calculate_max_drawdown(self, equity_history):

        if not equity_history:
            return 0

        peak = equity_history[0]

        max_drawdown = 0

        for value in equity_history:

            if value > peak:
                peak = value

            drawdown = (
                (value - peak)
                /
                peak
            )

            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown * 100



    def calculate_calmar(
        self,
        equity_history,
        periods_per_year=DEFAULT_PERIODS_PER_YEAR
    ):
        """
        Annualized return divided by the magnitude of max drawdown.
        Rewards strategies that compound steadily without large
        peak-to-trough losses, even if their Sharpe is unremarkable.
        Returns 0 if there's no drawdown or insufficient history
        (rather than dividing by zero / returning infinity, which
        isn't a meaningful "score").
        """

        if len(equity_history) < 2 or equity_history[0] == 0:
            return 0

        total_periods = len(equity_history) - 1

        total_return = (
            equity_history[-1] / equity_history[0]
        ) - 1

        years = total_periods / periods_per_year

        if years <= 0:
            return 0

        annualized_return = (1 + total_return) ** (1 / years) - 1 if (
            1 + total_return
        ) > 0 else -1

        max_drawdown_pct = abs(self.calculate_max_drawdown(equity_history))

        if max_drawdown_pct == 0:
            return 0

        return (annualized_return * 100) / max_drawdown_pct



    def calculate_profit_factor(self, returns):
        """
        Sum of gains / sum of losses (both taken as positive
        magnitudes). > 1 means gains outweighed losses. Returns None
        if there were no losing periods (undefined / infinite ratio)
        so callers can decide how to display that case rather than
        silently getting a misleading number.
        """

        gains = sum(r for r in returns if r > 0)
        losses = sum(-r for r in returns if r < 0)

        if losses == 0:
            return None

        return gains / losses



    def calculate_win_rate(self, returns):
        """
        Fraction of periods with a strictly positive return.
        """

        if not returns:
            return 0.0

        wins = sum(1 for r in returns if r > 0)

        return wins / len(returns)
