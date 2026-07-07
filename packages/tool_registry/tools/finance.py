"""Finance analysis tool — yfinance stock/crypto data."""

from __future__ import annotations

import os

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")


@tool(
    "finance_analysis",
    "Analyze stock or cryptocurrency data. Returns price history, key metrics, and summary.",
    sandbox_policy=SandboxPolicy(
        network_access=True,
        timeout_seconds=30,
    ),
)
def finance_analysis(
    symbol: str,
    period: str = "1mo",
    metrics: str = "price,volume,summary",
) -> str:
    """Analyze a stock or crypto symbol.

    Args:
        symbol: Ticker symbol (e.g., AAPL, BTC-USD, ETH-USD).
        period: Data period — 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max.
        metrics: Comma-separated list of metrics: price, volume, summary, dividends, splits.
    """
    try:
        import yfinance as yf
    except ImportError:
        return "Error: yfinance not installed. Run: pip install yfinance"

    try:
        ticker = yf.Ticker(symbol)
    except Exception as e:
        return f"Error: Could not fetch data for '{symbol}': {e}"

    requested = [m.strip() for m in metrics.split(",")]
    parts: list[str] = [f"## {symbol} Analysis\n"]

    if "price" in requested or "summary" in requested:
        try:
            hist = ticker.history(period=period)
            if hist.empty:
                parts.append(f"No price data available for {symbol} (period={period}).")
            else:
                latest = hist.iloc[-1]
                first = hist.iloc[0]
                change_pct = ((latest["Close"] - first["Close"]) / first["Close"]) * 100
                parts.append(
                    f"**Price (period: {period})**\n"
                    f"- Current: ${latest['Close']:.2f}\n"
                    f"- Open: ${first['Open']:.2f}\n"
                    f"- High: ${hist['High'].max():.2f}\n"
                    f"- Low: ${hist['Low'].min():.2f}\n"
                    f"- Change: {change_pct:+.2f}%\n"
                )
        except Exception as e:
            parts.append(f"Price data error: {e}")

    if "volume" in requested:
        try:
            hist = ticker.history(period=period)
            if not hist.empty:
                avg_vol = hist["Volume"].mean()
                max_vol = hist["Volume"].max()
                parts.append(
                    f"**Volume**\n"
                    f"- Average: {avg_vol:,.0f}\n"
                    f"- Max: {max_vol:,.0f}\n"
                )
        except Exception as e:
            parts.append(f"Volume data error: {e}")

    if "dividends" in requested:
        try:
            divs = ticker.dividends
            if divs is not None and not divs.empty:
                recent = divs.tail(5)
                parts.append(f"**Recent Dividends**\n{recent.to_string()}\n")
        except Exception:
            pass

    if "summary" in requested:
        try:
            info = ticker.info
            useful_keys = ["sector", "industry", "marketCap", "peRatio", "forwardPE", "dividendYield", "fiftyTwoWeekHigh", "fiftyTwoWeekLow"]
            summary_items = []
            for key in useful_keys:
                val = info.get(key) or info.get(key.lower())
                if val is not None:
                    summary_items.append(f"- {key}: {val}")
            if summary_items:
                parts.append("**Key Metrics**\n" + "\n".join(summary_items) + "\n")
        except Exception:
            pass

    return "\n".join(parts) if len(parts) > 1 else f"No data returned for {symbol}."
