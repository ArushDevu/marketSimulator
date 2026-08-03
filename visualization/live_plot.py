import matplotlib.pyplot as plt


class LivePlot:
    """
    Live dashboard showing market price and trader returns.
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

        self.prices = []

        self.return_history = {}



    def update(
        self,
        step,
        price,
        return_history
    ):

        if price is None:
            return


        self.steps.append(step)

        self.prices.append(price)

        self.return_history = return_history



        #
        # Price chart
        #

        self.price_ax.clear()


        self.price_ax.plot(
            self.steps,
            self.prices,
            linewidth=2,
            label="AAPL"
        )


        self.price_ax.set_title(
            "Live Stock Price"
        )


        self.price_ax.set_ylabel(
            "Price"
        )


        self.price_ax.grid(True)

        self.price_ax.legend()



        #
        # Return chart
        #

        self.return_ax.clear()


        colors = {
            "Trader 1": "blue",
            "Trader 2": "green",
            "Momentum Trader": "orange",
            "Market Maker": "red",
            "Mean Reversion Trader": "purple"
        }



        for trader_name, history in self.return_history.items():


            self.return_ax.plot(
                range(len(history)),
                history,
                label=trader_name,
                color=colors.get(trader_name),
                linewidth=2
            )



        self.return_ax.set_title(
            "Trader Returns"
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
