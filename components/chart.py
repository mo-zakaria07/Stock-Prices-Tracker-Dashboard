"""Matplotlib chart builders for price history and multi-ticker comparison."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

BG_COLOR = "#0e1117"
GRID_COLOR = "#2a2f3a"
SPINE_COLOR = "#3f4655"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT_COLOR = "#9ca3af"

POSITIVE_COLOR = "#22c55e"
NEGATIVE_COLOR = "#ef4444"
NEUTRAL_COLOR = "#3b82f6"
LINE_COLORS = ["#60a5fa", "#f87171", "#4ade80", "#fbbf24"]


def _style_axes(ax: plt.Axes) -> None:
    """Apply a dark, minimal style to a chart's axes."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, alpha=0.7)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=MUTED_TEXT_COLOR, labelsize=9)


def build_price_chart(history: pd.DataFrame, ticker: str, range_label: str) -> plt.Figure:
    """Build a single-ticker price history line chart for the given range."""
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=BG_COLOR)
    series = history[ticker]

    color = NEUTRAL_COLOR
    if len(series) >= 2:
        color = POSITIVE_COLOR if series.iloc[-1] >= series.iloc[0] else NEGATIVE_COLOR

    ax.plot(series.index, series.values, color=color, linewidth=1.8)
    ax.fill_between(series.index, series.values, series.min(), color=color, alpha=0.12)
    ax.set_title(f"{ticker} · {range_label}", fontsize=12, color=TEXT_COLOR, loc="left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def build_comparison_chart(histories: dict[str, pd.DataFrame], range_label: str) -> plt.Figure:
    """Build an overlaid comparison chart normalizing each ticker's series to 100."""
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG_COLOR)

    for idx, (ticker, history) in enumerate(histories.items()):
        series = history[ticker].dropna()
        if series.empty:
            continue
        normalized = series / series.iloc[0] * 100
        color = LINE_COLORS[idx % len(LINE_COLORS)]
        ax.plot(normalized.index, normalized.values, label=ticker, color=color, linewidth=1.8)

    ax.axhline(100, color=MUTED_TEXT_COLOR, linewidth=0.8, linestyle="--")
    ax.set_title(f"Normalized Comparison · {range_label}", fontsize=12, color=TEXT_COLOR, loc="left")
    ax.set_ylabel("Indexed to 100", fontsize=9, color=MUTED_TEXT_COLOR)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    legend = ax.legend(frameon=False, fontsize=9, loc="upper left", labelcolor=TEXT_COLOR)
    _style_axes(ax)
    fig.tight_layout()
    return fig
