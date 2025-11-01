import pandas as pd
from plotly import graph_objs as go
from .strategy import Strategy
from typing import Any


class Momentum(Strategy):
    def __init__(self, data: pd.DataFrame, st: Any):
        self.name = "Momentum Strategy"
        self.lookback_window = 20
        self.data = data
        self.st = st

    def execute(self):
        self.st.subheader("Momentum Strategy Parameters")
        self.st.write(
            "The momentum strategy uses the rate of change of closing prices to generate buy and sell signals. Change the lookback period below to generate different buy/sell signals."
        )

        self.lookback_window = self.st.number_input(
            "Lookback Window (days):",
            min_value=1,
            value=self.lookback_window,
        )

        self.run()
        self.generate_plotly()

    def run(self):
        signals = pd.DataFrame(index=self.data.index)
        signals["close"] = self.data["close"]
        signals["momentum"] = self.data["close"].pct_change(self.lookback_window)
        signals["signal"] = 0
        signals["signal"][self.lookback_window :] = (
            signals["momentum"][self.lookback_window :] > 0
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
                y=self.data["momentum"],
                mode="lines",
                name=f"Momentum ({self.lookback_window} days)",
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
