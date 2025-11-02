import pandas as pd
from plotly import graph_objs as go
from .strategy import Strategy
from typing import Any


class BollingerBandsStrategy(Strategy):
    def __init__(self, data: pd.DataFrame, st: Any):
        self.name = "Bollinger Band Strategy"
        self.window = 20
        self.multiple = 2.0
        self.data = data
        self.st = st
        self.signals = pd.DataFrame(index=self.data.index)

    def execute(self):
        self.st.subheader("Bollinger Band Strategy")

        self.st.write(
            "Bollinger band strategy uses moving averages and standard deviations to create upper and lower bands. Buy signals are generated when the price crosses below the lower band, and sell signals are generated when the price crosses above the upper band. The Bollinger bands strategy only uses closing prices to generate buy and sell signals. Adjust the average window and standard deviation multiple below to see how the bands and signals change."
        )

        col1, col2 = self.st.columns(2)
        with col1:
            self.short_window = self.st.number_input(
                "Average Window (days):",
                min_value=1,
                value=self.window,
            )

        with col2:
            self.multiple = self.st.number_input(
                "Standard Deviation Multiple:",
                min_value=0.1,
                value=self.multiple,
                step=0.1,
            )
        self.run_algorithm()
        self.generate_plotly()

    def run_algorithm(self):
        self.signals["close"] = self.data["close"]

        # new implementation
        self.signals["middle"] = self.data["close"].rolling(window=self.window).mean()
        self.signals["std"] = (
            self.data["close"].rolling(window=self.window).std()
        )  # std calculates the rolling standard deviation
        self.signals["high"] = self.signals["middle"] + (
            self.signals["std"] * self.multiple
        )
        self.signals["low"] = self.signals["middle"] - (
            self.signals["std"] * self.multiple
        )

        self.signals["signal"] = 0
        self.signals["signal"][
            self.data["close"] < self.signals["low"]
        ] = 1  # buy signal
        self.signals["signal"][
            self.data["close"] > self.signals["high"]
        ] = -1  # sell signal

        self.signals["signal"] = self.signals["signal"].shift(1)

    def generate_plotly(self):
        if self.data is None:
            raise ValueError("No data to plot. Please run the strategy first.")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.signals["close"],
                mode="lines",
                name="Closing Price",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.signals["middle"],
                mode="lines",
                name="Middle Band",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.signals["high"],
                mode="lines",
                name="Upper band",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.signals["low"],
                mode="lines",
                name="Lower band",
            )
        )

        buy_signals = self.signals[self.signals["signal"] == 1]
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals["close"],
                mode="markers",
                marker=dict(color="green", size=10, symbol="triangle-up"),
                name="Buy Signal",
            )
        )

        sell_signals = self.signals[self.signals["signal"] == -1]
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=sell_signals["close"],
                mode="markers",
                marker=dict(color="red", size=10, symbol="triangle-down"),
                name="Sell Signal",
            )
        )

        fig.update_layout(
            title="Bollinger Band Strategy Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Legend",
        )

        self.st.plotly_chart(fig)
