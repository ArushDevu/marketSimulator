import math


class PerformanceAnalyzer:
    """
    Calculates trading performance metrics.
    """

    def calculate_returns(self, equity_history):
        """
        Converts net worth history into percentage returns.
        """

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



    def calculate_sharpe(self, returns):

        if len(returns) < 2:
            return 0


        mean_return = sum(returns) / len(returns)


        variance = sum(
            (r - mean_return) ** 2
            for r in returns
        ) / (len(returns)-1)


        volatility = math.sqrt(
            variance
        )


        if volatility == 0:
            return 0


        return mean_return / volatility



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
