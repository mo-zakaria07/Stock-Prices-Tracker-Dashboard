"""Streamlit entry point for the Stock Price Tracker Dashboard."""

import time
from datetime import datetime

import streamlit as st

from components import chart
from data import db
from data.fetcher import TickerFetchError, fetch_price_history, fetch_quote

REFRESH_INTERVAL_SECONDS = 300
RANGE_OPTIONS = ["1W", "1M", "3M", "1Y"]


def render_sidebar(watchlist: list[str]) -> None:
    """Render sidebar controls for adding and removing watchlist tickers."""
    st.sidebar.header("Watchlist")

    with st.sidebar.form("add_ticker_form", clear_on_submit=True):
        new_ticker = st.text_input("Add ticker", placeholder="e.g. AAPL").strip().upper()
        submitted = st.form_submit_button("Add")
        if submitted and new_ticker:
            if new_ticker in watchlist:
                st.sidebar.warning(f"{new_ticker} is already on your watchlist.")
            else:
                with st.spinner(f"Validating {new_ticker}..."):
                    try:
                        fetch_quote(new_ticker)
                        db.add_ticker(new_ticker)
                        st.sidebar.success(f"Added {new_ticker}.")
                        st.rerun()
                    except TickerFetchError:
                        st.sidebar.error(f"'{new_ticker}' is not a valid ticker.")

    if watchlist:
        st.sidebar.subheader("Remove")
        for ticker in watchlist:
            col1, col2 = st.sidebar.columns([3, 1])
            col1.write(ticker)
            if col2.button("✕", key=f"remove_{ticker}"):
                db.remove_ticker(ticker)
                st.rerun()
    else:
        st.sidebar.info("No tickers yet. Add one above.")


def render_quote_cards(watchlist: list[str]) -> None:
    """Render a metric card row for every ticker in the watchlist."""
    for ticker in watchlist:
        try:
            quote = fetch_quote(ticker)
        except TickerFetchError as exc:
            st.error(str(exc))
            continue

        st.subheader(ticker)
        cols = st.columns(6)
        cols[0].metric("Price", f"${quote['current_price']:.2f}")
        cols[1].metric(
            "Change ($)",
            f"${quote['change']:.2f}",
            delta=f"{quote['change']:.2f}",
        )
        cols[2].metric(
            "Change (%)",
            f"{quote['change_pct']:.2f}%",
            delta=f"{quote['change_pct']:.2f}%",
        )
        cols[3].metric("52W High", f"${quote['year_high']:.2f}")
        cols[4].metric("52W Low", f"${quote['year_low']:.2f}")
        cols[5].metric("Volume", f"{quote['volume']:,}")


def render_price_history(watchlist: list[str]) -> None:
    """Render a single-ticker price history chart with a range selector."""
    st.divider()
    st.subheader("Price History")

    selected_ticker = st.selectbox("Ticker", watchlist, key="history_ticker")
    range_label = st.radio("Range", RANGE_OPTIONS, horizontal=True, key="history_range")

    try:
        history = fetch_price_history(selected_ticker, range_label)
        fig = chart.build_price_chart(history, selected_ticker, range_label)
        st.pyplot(fig)
    except TickerFetchError as exc:
        st.error(str(exc))


def render_comparison_chart(watchlist: list[str]) -> None:
    """Render an overlaid, normalized comparison chart for up to 4 tickers."""
    st.divider()
    st.subheader("Compare Tickers")

    default_selection = watchlist[: min(2, len(watchlist))]
    selected = st.multiselect(
        "Select up to 4 tickers to compare",
        watchlist,
        default=default_selection,
        max_selections=4,
        key="comparison_tickers",
    )
    if not selected:
        st.info("Select at least one ticker to compare.")
        return

    range_label = st.radio("Comparison Range", RANGE_OPTIONS, horizontal=True, key="comparison_range")

    histories = {}
    for ticker in selected:
        try:
            histories[ticker] = fetch_price_history(ticker, range_label)
        except TickerFetchError as exc:
            st.error(str(exc))

    if histories:
        fig = chart.build_comparison_chart(histories, range_label)
        st.pyplot(fig)


def run_countdown_and_refresh(placeholder: "st.delta_generator.DeltaGenerator") -> None:
    """Block for the refresh interval, showing a live countdown, then rerun the app.

    Clears the data caches once the countdown reaches zero so the next rerun
    fetches fresh quotes and history, satisfying the 5-minute auto-refresh.
    """
    for remaining in range(REFRESH_INTERVAL_SECONDS, 0, -1):
        minutes, seconds = divmod(remaining, 60)
        placeholder.caption(f"⏱ Next refresh in {minutes:02d}:{seconds:02d}")
        time.sleep(1)

    fetch_quote.clear()
    fetch_price_history.clear()
    st.rerun()


def main() -> None:
    """Configure the page and render the full dashboard."""
    st.set_page_config(page_title="Stock Price Tracker", layout="wide", page_icon="📈")

    st.title("📈 Stock Price Tracker Dashboard")

    watchlist = db.get_watchlist()
    render_sidebar(watchlist)
    watchlist = db.get_watchlist()

    header_col, status_col = st.columns([4, 1])
    header_col.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    countdown_placeholder = status_col.empty()

    if not watchlist:
        st.info("Add a ticker from the sidebar to get started.")
    else:
        render_quote_cards(watchlist)
        render_price_history(watchlist)
        render_comparison_chart(watchlist)

    run_countdown_and_refresh(countdown_placeholder)


if __name__ == "__main__":
    main()
