import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import math
import pandas as pd
from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.data import get_historical_data, get_stock_info
from strategies.moving_average import MovingAverageStrategy
from strategies.momentum import MomentumStrategy
from strategies.bollinger_bands import BollingerBandsStrategy
from strategies.volume_spike import VolumeSpikeStrategy

pd.options.mode.chained_assignment = None

app = FastAPI(title="Portfolio Backtester API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Mock Streamlit – lets us instantiate strategy classes without Streamlit
# ---------------------------------------------------------------------------

class _MockCol:
    def number_input(self, label: str, **kwargs: Any) -> Any:
        return kwargs.get("value", 0)

    def __enter__(self) -> "_MockCol":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class _MockSt:
    def subheader(self, *args: Any, **kwargs: Any) -> None:
        pass

    def write(self, *args: Any, **kwargs: Any) -> None:
        pass

    def columns(self, n: int) -> list[_MockCol]:
        return [_MockCol() for _ in range(n)]

    def number_input(self, label: str, **kwargs: Any) -> Any:
        return kwargs.get("value", 0)

    def plotly_chart(self, *args: Any, **kwargs: Any) -> None:
        pass


MOCK_ST = _MockSt()


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------

STRATEGIES = [
    {
        "id": "moving_average",
        "name": "Moving Average Crossover",
        "description": (
            "Triggers a buy when the short-term MA crosses above the long-term MA, "
            "and a sell when it crosses below."
        ),
        "params": [
            {
                "name": "short_window",
                "label": "Short Window (days)",
                "default": 50,
                "min": 1,
                "max": 200,
                "step": 1,
                "type": "number",
            },
            {
                "name": "long_window",
                "label": "Long Window (days)",
                "default": 200,
                "min": 2,
                "max": 500,
                "step": 1,
                "type": "number",
            },
        ],
    },
    {
        "id": "momentum",
        "name": "Momentum",
        "description": (
            "Generates buy signals when price has increased over the lookback window, "
            "sell signals when it has decreased."
        ),
        "params": [
            {
                "name": "lookback_window",
                "label": "Lookback Window (days)",
                "default": 20,
                "min": 1,
                "max": 200,
                "step": 1,
                "type": "number",
            },
        ],
    },
    {
        "id": "bollinger_bands",
        "name": "Bollinger Bands",
        "description": (
            "Buy when price crosses below the lower band; "
            "sell when it crosses above the upper band."
        ),
        "params": [
            {
                "name": "window",
                "label": "Average Window (days)",
                "default": 20,
                "min": 2,
                "max": 200,
                "step": 1,
                "type": "number",
            },
            {
                "name": "multiple",
                "label": "Std Dev Multiple",
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "step": 0.1,
                "type": "number",
            },
        ],
    },
    {
        "id": "volume_spike",
        "name": "Volume Spike",
        "description": (
            "Triggers buy/sell when trading volume spikes significantly "
            "above its moving average."
        ),
        "params": [
            {
                "name": "window",
                "label": "Volume MA Window (days)",
                "default": 50,
                "min": 2,
                "max": 200,
                "step": 1,
                "type": "number",
            },
            {
                "name": "multiplier",
                "label": "Spike Multiplier",
                "default": 1.5,
                "min": 1.1,
                "max": 5.0,
                "step": 0.1,
                "type": "number",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(value: Any) -> Any:
    """Convert NaN / inf to None so FastAPI can serialise to JSON."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for idx, row in df.iterrows():
        record: dict = {"date": str(idx.date()) if hasattr(idx, "date") else str(idx)}
        for col in df.columns:
            record[col] = _clean(row[col])
        records.append(record)
    return records


def _run_moving_average(data: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, list[dict]]:
    strategy = MovingAverageStrategy(data.copy(), MOCK_ST)
    strategy.short_window = int(params.get("short_window", 50))
    strategy.long_window = int(params.get("long_window", 200))
    strategy._run_algorithm()
    indicators = [
        {"key": "short_ma", "label": f"Short MA ({strategy.short_window}d)", "secondary": False, "color": "#3b82f6"},
        {"key": "long_ma", "label": f"Long MA ({strategy.long_window}d)", "secondary": False, "color": "#f59e0b"},
    ]
    return strategy.data, indicators


def _run_momentum(data: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, list[dict]]:
    strategy = MomentumStrategy(data.copy(), MOCK_ST)
    strategy.lookback_window = int(params.get("lookback_window", 20))
    strategy._run_algorithm()
    indicators = [
        {"key": "momentum", "label": f"Momentum ({strategy.lookback_window}d %chg)", "secondary": True, "color": "#8b5cf6"},
    ]
    return strategy.data, indicators


def _run_bollinger_bands(data: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, list[dict]]:
    strategy = BollingerBandsStrategy(data.copy(), MOCK_ST)
    strategy.window = int(params.get("window", 20))
    strategy.multiple = float(params.get("multiple", 2.0))
    strategy._run_algorithm()
    indicators = [
        {"key": "middle", "label": f"Middle Band ({strategy.window}d)", "secondary": False, "color": "#3b82f6"},
        {"key": "high", "label": "Upper Band", "secondary": False, "color": "#64748b"},
        {"key": "low", "label": "Lower Band", "secondary": False, "color": "#64748b"},
    ]
    return strategy.signals, indicators


def _run_volume_spike(data: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, list[dict]]:
    window = int(params.get("window", 50))
    multiplier = float(params.get("multiplier", 1.5))

    signals = pd.DataFrame(index=data.index)
    signals["close"] = data["close"]
    signals["volume"] = data["volume"]
    signals["volume_ma"] = data["volume"].rolling(window).mean()
    signals["signal"] = 0
    signals.loc[signals.index[window:], "signal"] = (
        signals["volume"].iloc[window:] > multiplier * signals["volume_ma"].iloc[window:]
    ).astype(int)
    signals["signal"] = signals["signal"].diff()

    indicators = [
        {"key": "volume_ma", "label": f"Volume MA ({window}d)", "secondary": True, "color": "#f59e0b"},
        {"key": "volume", "label": "Volume", "secondary": True, "color": "#6b7280"},
    ]
    return signals, indicators


STRATEGY_RUNNERS = {
    "moving_average": _run_moving_average,
    "momentum": _run_momentum,
    "bollinger_bands": _run_bollinger_bands,
    "volume_spike": _run_volume_spike,
}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    strategy: str
    params: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/strategies")
def list_strategies():
    return STRATEGIES


@app.get("/api/stock-info/{ticker}")
def stock_info(ticker: str):
    info = get_stock_info(ticker.upper())
    if info is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
    return {
        "name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "website": info.get("website", ""),
        "summary": info.get("longBusinessSummary", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "currency": info.get("currency", "USD"),
    }


@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    if req.strategy not in STRATEGY_RUNNERS:
        raise HTTPException(status_code=400, detail=f"Unknown strategy '{req.strategy}'.")

    try:
        start = date.fromisoformat(req.start_date)
        end = date.fromisoformat(req.end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {exc}") from exc

    try:
        data = get_historical_data(req.ticker.upper(), start, end)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data: {exc}") from exc

    if data.empty:
        raise HTTPException(status_code=404, detail="No data returned for the given ticker and date range.")

    # Flatten MultiIndex columns that newer yfinance may produce
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]

    runner = STRATEGY_RUNNERS[req.strategy]
    try:
        result_df, indicators = runner(data, req.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Strategy error: {exc}") from exc

    chart_data = _df_to_records(result_df)

    buy_count = sum(1 for r in chart_data if r.get("signal") == 1)
    sell_count = sum(1 for r in chart_data if r.get("signal") == -1)

    return {
        "chart_data": chart_data,
        "indicators": indicators,
        "stats": {
            "total_signals": buy_count + sell_count,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
        },
    }
