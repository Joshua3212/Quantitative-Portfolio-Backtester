import yfinance
import datetime
import pandas as pd


def get_stock_info(abbreviation: str) -> dict | None:
    if bool(yfinance.Ticker(abbreviation).info.get("symbol")):
        return yfinance.Ticker(abbreviation).info
    return None


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
