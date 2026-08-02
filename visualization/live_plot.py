import matplotlib.pyplot as plt


class LivePlot:
    """
    Live price chart for the market simulator.
    """

    def __init__(self):

        plt.ion()

        self.fig, self.ax = plt.subplots(figsize=(10, 5))

        self.prices = []
        self.steps = []



    def update(self, step, price):

        if price is None:
            return

        self.steps.append(step)
        self.prices.append(price)

        self.ax.clear()

        self.ax.plot(
            self.steps,
            self.prices,
            linewidth=2,
            label="AAPL"
        )

        self.ax.set_title("Live Stock Price")

        self.ax.set_xlabel("Simulation Step")

        self.ax.set_ylabel("Price")

        self.ax.grid(True)

        self.ax.legend()

        plt.pause(0.001)



    def show(self):
        plt.ioff()
        plt.show()