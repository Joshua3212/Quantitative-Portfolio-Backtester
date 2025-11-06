import pandas as pd
from plotly import graph_objs as go
from .strategy import Strategy
from typing import Any


class MomentumStrategy(Strategy):
    def __init__(self, data: pd.DataFrame, st: Any):
        self.name = "Momentum Strategy"
        self.data = data
        self.st = st

        self.lookback_window = 20

        self.signals = pd.DataFrame(index=self.data.index)

    def execute(self):
        self._render_inputs()
        self._run_algorithm()
        self._generate_plotly_chart()

    def _render_inputs(self):
        self.st.subheader(self.name)
        self.st.write(
            "The momentum strategy generates buy signals when the price has increased over a specified lookback window, and sell signals when the price has decreased over that window. It only uses closing prices to determine momentum. Adjust the lookback window below to see how buy and sell signals change."
        )

        self.lookback_window = self.st.number_input(
            "Lookback Window (days):",
            min_value=1,
            value=self.lookback_window,
        )

    def _run_algorithm(self):
        self.signals["close"] = self.data["close"]
        self.signals["momentum"] = self.data["close"].pct_change(self.lookback_window)
        self.signals["signal"] = 0
        self.signals["signal"][self.lookback_window :] = (
            self.signals["momentum"][self.lookback_window :] > 0
        ).astype(int)
        self.signals["signal"] = self.signals["signal"].diff()
        self.data = self.signals

    def _generate_plotly_chart(self):
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
            title="Momentum Strategy Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Legend",
        )

        self.st.plotly_chart(fig)
