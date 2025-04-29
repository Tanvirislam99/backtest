import streamlit as st
from bdshare import get_hist_data
from fastquant import backtest
import pandas as pd
from datetime import date

@st.cache_data
def fetch_data(symbol, start_date):
    try:
        df = get_hist_data(start_date, date.today(), symbol)
        df = df.drop(columns=["symbol", "ltp", "ycp", "trade", "value"])
        df.columns = ["High", "Low", "Open", "Close", "Volume"]
        df = df[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        df = df[df.Low != 0].sort_index()
        return df
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

def get_performance(result, strategy_name):
    perf, orders = result
    df = perf[["final_value", "pnl", "rtot", "rnorm", "sharperatio", "maxdrawdown"]].copy()
    df["trade_qty"] = len(orders["orders"])
    df["total_return(%)"] = 100 * df["rtot"]
    df["annual_return(%)"] = 100 * df["rnorm"]
    df["Strategy"] = strategy_name
    return df[["Strategy", "final_value", "pnl", "total_return(%)", "annual_return(%)", "sharperatio", "maxdrawdown", "trade_qty"]]

st.title("📈 DSE Stock Backtester - Bombay Premium Finance Lab")

symbol = st.text_input("Enter DSE Trading Code (e.g., WALTONHIL)", "WALTONHIL")
start_date = st.date_input("Start Date", value=date(2022, 1, 1))
strategy = st.selectbox("Choose Strategy", ["macd", "emac", "smac", "buynhold"])

if strategy == "macd":
    fast = st.slider("Fast Period", 2, 30, 12)
    slow = st.slider("Slow Period", 2, 50, 26)
    signal = st.slider("Signal Period", 2, 20, 9)
    params = {"fast_period": fast, "slow_period": slow, "signal_period": signal}
elif strategy in ["smac", "emac"]:
    fast = st.slider("Fast Period", 2, 30, 12)
    slow = st.slider("Slow Period", 2, 50, 26)
    params = {"fast_period": fast, "slow_period": slow}
else:
    params = {}

run = st.button("Run Backtest")

if run:
    df = fetch_data(symbol, start_date)
    if not df.empty:
        result = backtest(strategy, df, commission=0.004, return_history=True, verbose=False, **params)
        perf_df = get_performance(result, strategy.upper())
        st.subheader("📊 Performance Summary")
        st.dataframe(perf_df)
        st.subheader("📈 Equity Curve")
        result[0]["equity_curve"].plot(title="Equity Curve")
        st.pyplot()
    else:
        st.warning("No data returned. Please check the symbol or try a different date range.")
