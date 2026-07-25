"""SQLite persistence layer for the watchlist."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "watchlist.db"


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection to the watchlist database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    return conn


def add_ticker(ticker: str) -> None:
    """Add a ticker symbol to the watchlist (no-op if it already exists)."""
    ticker = ticker.strip().upper()
    if not ticker:
        return
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker,))
        conn.commit()
    finally:
        conn.close()


def remove_ticker(ticker: str) -> None:
    """Remove a ticker symbol from the watchlist."""
    ticker = ticker.strip().upper()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.commit()
    finally:
        conn.close()


def get_watchlist() -> list[str]:
    """Return all tickers currently in the watchlist, sorted alphabetically."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT ticker FROM watchlist ORDER BY ticker ASC").fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()
