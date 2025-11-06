import pandas as pd
from plotly import graph_objs as go
from .strategy import Strategy
from typing import Any


class VolumeSpikeStrategy(Strategy):
    def __init__(self, data: pd.DataFrame, st: Any):
        self.name = "Volume Spike Strategy"
        self.data = data
        self.st = st

        self.window = 50

        self.signals = pd.DataFrame(index=self.data.index)

    def execute(self):
        self._render_inputs()
        self._run_algorithm()
        self._generate_plotly()

    def _render_inputs(self):
        self.st.subheader(self.name)
        self.st.write(
            "The volume spike strategy triggers when a sudden spike in volume is detected compared to the average volume over a specified lookback period. It uses volume data to generate buy and sell signals. Adjust the volume moving average window below to see how buy and sell signals change. To get a better view of when buy/sell signals occur click on the 'Volume MA' and 'Trading Volume' texts in the legend on the right to hide it from the plot."
        )

        self.window = self.st.number_input(
            "Volume Moving Average Window (days):",
            min_value=1,
            value=self.window,
        )

    def _run_algorithm(self):
        self.signals["close"] = self.data["close"]
        self.signals["volume"] = self.data["volume"]

        self.signals["volume_ma"] = self.data["volume"].rolling(self.window).mean()

        self.signals["signal"] = 0
        self.signals["signal"][self.window :] = (
            self.signals["volume"][self.window :]
            > 1.5 * self.signals["volume_ma"][self.window :]
        ).astype(int)
        self.signals["signal"] = self.signals["signal"].diff()

        self.data = self.signals

    def _generate_plotly(self):
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
                y=self.signals["volume"],
                mode="lines",
                name="Trading Volume",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.signals["volume_ma"],
                mode="lines",
                name=f"Volume MA ({self.window} days)",
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
            title="Moving Average Strategy Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Legend",
        )

        self.st.plotly_chart(fig)
