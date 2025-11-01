import pandas as pd
from plotly import graph_objs as go
from .strategy import Strategy
from typing import Any


class MovingAverageStrategy(Strategy):
    def __init__(self, data: pd.DataFrame, st: Any):
        self.name = "Moving Average Strategy"
        self.short_window = 50
        self.long_window = 200
        self.data = data
        self.st = st

    def execute(self):
        self.st.subheader("Moving Average Strategy Parameters")
        self.st.write(
            "The moving average strategy uses two moving averages to generate buy and sell signals. Change the short/long moving average windows below to generate different buy/sell signals."
        )
        col1, col2 = self.st.columns(2)
        with col1:
            self.short_window = self.st.number_input(
                "Short Moving Average Window (days):",
                min_value=1,
                value=self.short_window,
            )
        with col2:
            self.long_window = self.st.number_input(
                "Long Moving Average Window (days):",
                min_value=1,
                value=self.long_window,
            )

        self.run_algorithm()
        self.generate_plotly()

    def run_algorithm(self):
        signals = pd.DataFrame(index=self.data.index)
        signals["close"] = self.data["close"]
        signals["short_ma"] = self.data["close"].rolling(self.short_window).mean()
        signals["long_ma"] = self.data["close"].rolling(self.long_window).mean()
        signals["signal"] = 0
        signals["signal"][self.short_window :] = (
            signals["short_ma"][self.short_window :]
            > signals["long_ma"][self.short_window :]
        ).astype(int)
        signals["signal"] = signals["signal"].diff()
        self.data = signals

    def generate_plotly(self):
        if self.data is None:
            raise ValueError("No data to plot. Please run the strategy first.")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data["close"],
                mode="lines",
                name="Closing Price",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data["short_ma"],
                mode="lines",
                name=f"Short MA ({self.short_window} days)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data["long_ma"],
                mode="lines",
                name=f"Long MA ({self.long_window} days)",
            )
        )

        buy_signals = self.data[self.data["signal"] == 1]
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals["close"],
                mode="markers",
                marker=dict(color="green", size=10, symbol="triangle-up"),
                name="Buy Signal",
            )
        )

        sell_signals = self.data[self.data["signal"] == -1]
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
            title="Moving Average Strategy Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Legend",
        )

        self.st.plotly_chart(fig, use_container_width=True)
