import yfinance
import datetime
import pandas as pd


def check_if_stock_exists(abbreviation: str) -> bool:
    return bool(yfinance.Ticker(abbreviation).info.get("symbol"))


def get_historical_data(
    symbol: str, start_date: datetime.date, end_date: datetime.date
) -> pd.DataFrame:

    res = yfinance.download(symbol, start=start_date, end=end_date)
    df = pd.DataFrame()

    df["close"] = res["Close"]  # type: ignore
    df["open"] = res["Open"]  # type: ignore
    df["high"] = res["High"]  # type: ignore
    df["low"] = res["Low"]  # type: ignore
    df["volume"] = res["Volume"]  # type: ignore
    return df
