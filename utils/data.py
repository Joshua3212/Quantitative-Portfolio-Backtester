import yfinance
import datetime
import pandas as pd


def check_if_stock_exists(abbreviation: str) -> bool:
    return bool(yfinance.Ticker(abbreviation).info.get("symbol"))


def get_historical_data(
    symbol: str, start_date: datetime.date, end_date: datetime.date
) -> pd.DataFrame:
    ticker = yfinance.Ticker(symbol)
    res = ticker.history(start=start_date, end=end_date)
    df = pd.DataFrame()

    df["close"] = res["Close"]
    df["open"] = res["Open"]
    df["high"] = res["High"]
    df["low"] = res["Low"]
    df["volume"] = res["Volume"]
    return df
