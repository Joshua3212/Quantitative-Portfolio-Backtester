import streamlit as st
import datetime
from utils import data
from strategies.moving_average import MovingAverageStrategy
from strategies.momentum import Momentum
import re

st.set_page_config(layout="wide")
st.title("Quantitative Portfolio Backtester")
st.write("Welcome to the Quantitative Portfolio Backtester web application!")
st.write(
    "To get started simply enter the stock abreviation, daterange and the strategies you wish to apply to the data below."
)

col1, col2, col3 = st.columns(3)
stock_symbol = None
date_range = None
run = False
stock_exists = False

# edit this list to add new strategies
strategies = [MovingAverageStrategy, Momentum]
strategy_name = None
strategy_names = [" ".join(re.findall("[A-Z][a-z]*", s.__name__)) for s in strategies]
strategy_class = None

with col1:
    if strategy_name := st.selectbox(
        "Select a strategy to apply:",
        strategy_names,
    ):
        strategy_index = strategy_names.index(strategy_name)
        strategy_class = strategies[strategy_index]


with col2:
    stock_symbol = st.text_input("Stock Abreviation", placeholder="AAPL")

with col3:
    date_range = st.date_input("Select date range", [], max_value=datetime.date.today())


if not date_range or not len(date_range) == 2:
    st.info("Please select a start and end date for the date range.")
if not stock_symbol:
    st.info("Please enter a stock abreviation to proceed.")

if stock_symbol:
    stock_exists = data.check_if_stock_exists(stock_symbol)
    if stock_exists:
        st.success(f"Stock {stock_symbol} found!")
    else:
        st.error(f"Stock {stock_symbol} not found. Please check the abreviation.")


if (
    stock_symbol
    and stock_exists
    and date_range
    and len(date_range) == 2
    and strategy_class
):
    start_date, end_date = sorted(date_range)
    data = data.get_historical_data(
        stock_symbol,
        start_date,
        end_date,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(
            f"Historical Data for {stock_symbol} from {start_date} to {end_date}"
        )
        st.write(
            "The below graph shows the historical data from Yahoo Fiance for the selected stock and date range."
        )

        st.line_chart(data.close)
    with col2:
        strategy = strategy_class(data, st)
        strategy.execute()
