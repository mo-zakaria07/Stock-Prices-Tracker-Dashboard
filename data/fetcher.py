"""All yfinance data access, wrapped with 5-minute Streamlit caching."""

import pandas as pd
import streamlit as st
import yfinance as yf

CACHE_TTL_SECONDS = 300

# Maps a UI range label to a (period, interval) pair understood by yfinance.
RANGE_TO_PERIOD = {
    "1W": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "1Y": ("1y", "1d"),
}


class TickerFetchError(Exception):
    """Raised when a ticker's data cannot be retrieved or is invalid."""


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_quote(ticker: str) -> dict:
    """Fetch current price, daily change, 52-week high/low, and volume for a ticker.

    Raises:
        TickerFetchError: if the ticker is invalid or the network call fails.
    """
    try:
        hist = yf.Ticker(ticker).history(period="1y")
    except Exception as exc:
        raise TickerFetchError(f"Network error fetching {ticker}: {exc}") from exc

    if hist.empty:
        raise TickerFetchError(f"No data found for ticker '{ticker}'. It may be invalid.")

    current_price = float(hist["Close"].iloc[-1])
    previous_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current_price
    change = current_price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    return {
        "ticker": ticker,
        "current_price": current_price,
        "change": change,
        "change_pct": change_pct,
        "year_high": float(hist["High"].max()),
        "year_low": float(hist["Low"].min()),
        "volume": int(hist["Volume"].iloc[-1]),
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_price_history(ticker: str, range_label: str) -> pd.DataFrame:
    """Fetch a price history DataFrame for a ticker over the given UI range label.

    Raises:
        TickerFetchError: if the ticker is invalid, the range is unknown, or the
            network call fails.
    """
    if range_label not in RANGE_TO_PERIOD:
        raise TickerFetchError(f"Unknown range '{range_label}'.")

    period, interval = RANGE_TO_PERIOD[range_label]
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception as exc:
        raise TickerFetchError(f"Network error fetching {ticker}: {exc}") from exc

    if hist.empty:
        raise TickerFetchError(f"No price history found for ticker '{ticker}'.")

    return hist[["Close"]].rename(columns={"Close": ticker})


def validate_ticker(ticker: str) -> bool:
    """Check whether a ticker symbol resolves to real yfinance data."""
    try:
        fetch_quote(ticker)
        return True
    except TickerFetchError:
        return False
