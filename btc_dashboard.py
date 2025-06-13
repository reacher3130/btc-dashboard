import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# ----- UI Setup -----
st.set_page_config(page_title="BTC 15-min Strategy", layout="wide")
st.title("💹 BTC/USDT 15-min Live Dashboard (MA20 & MA50 Strategy)")

# ----- Helper Functions -----
@st.cache_data(ttl=900)
def fetch_btc_ohlcv():
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": "15m", "limit": 200}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["low"] = df["low"].astype(float)
    df["high"] = df["high"].astype(float)
    return df[["time", "open", "high", "low", "close"]]

def detect_trade(df):
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()
    
    trades = []

    for i in range(50, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        
        rising = row["MA20"] > prev["MA20"] and row["MA50"] > prev["MA50"]
        falling = row["MA20"] < prev["MA20"] and row["MA50"] < prev["MA50"]

        # Bullish candle
        is_bullish = row["close"] > row["open"]
        is_bearish = row["close"] < row["open"]

        if rising and is_bullish and (
            abs(row["close"] - row["MA20"]) < 20 or abs(row["close"] - row["MA50"]) < 20):
            entry = row["close"]
            sl = row["low"]
            target = entry + 2 * (entry - sl)
            trades.append({"type": "Buy", "time": row["time"], "entry": entry, "sl": sl, "target": target})

        elif falling and is_bearish and (
            abs(row["close"] - row["MA20"]) < 20 or abs(row["close"] - row["MA50"]) < 20):
            entry = row["close"]
            sl = row["high"]
            target = entry - 2 * (sl - entry)
            trades.append({"type": "Sell", "time": row["time"], "entry": entry, "sl": sl, "target": target})
    
    return trades

# ----- Main App -----
df = fetch_btc_ohlcv()
st.line_chart(df.set_index("time")[["close", "MA20", "MA50"]] if "MA20" in df else df.set_index("time")["close"])

trades = detect_trade(df)
st.subheader("📊 Latest Trade Setups")
if trades:
    st.dataframe(pd.DataFrame(trades[-5:]))
else:
    st.info("No trade setups detected on latest candle.")

st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (auto every 15min)")
