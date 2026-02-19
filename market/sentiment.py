"""Alpha Vantage news sentiment wrapper."""

import requests
from rich.console import Console
from rich.table import Table
from rich import box

from models.profile import UserProfile
from ui.prompts import ask_string, pause
from config import ALPHA_VANTAGE_BASE_URL

console = Console()

# Session cache to avoid burning API calls
_sentiment_cache: dict[str, dict] = {}


def fetch_sentiment(ticker: str, api_key: str) -> dict | None:
    """Fetch news sentiment for a ticker from Alpha Vantage."""
    if ticker in _sentiment_cache:
        return _sentiment_cache[ticker]

    if not api_key:
        return None

    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": api_key,
            "limit": 5,
        }
        resp = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        data = resp.json()

        if "feed" not in data:
            return None

        articles = []
        total_score = 0
        count = 0

        for article in data["feed"][:5]:
            # Find sentiment for our specific ticker
            for ts in article.get("ticker_sentiment", []):
                if ts["ticker"] == ticker:
                    score = float(ts.get("ticker_sentiment_score", 0))
                    label = ts.get("ticker_sentiment_label", "Neutral")
                    articles.append({
                        "title": article.get("title", "")[:60],
                        "score": score,
                        "label": label,
                        "source": article.get("source", ""),
                    })
                    total_score += score
                    count += 1
                    break

        result = {
            "ticker": ticker,
            "avg_score": total_score / count if count else 0,
            "articles": articles,
            "count": count,
        }
        _sentiment_cache[ticker] = result
        return result

    except Exception:
        return None


def show_sentiment(profile: UserProfile):
    """Display news sentiment for watchlist tickers."""
    if not profile.alpha_vantage_key:
        console.print()
        console.print("[yellow]No Alpha Vantage API key set. Add one in Settings (option 7).[/]")
        console.print("[dim]Get a free key at https://www.alphavantage.co/support/#api-key[/]")
        pause()
        return

    ticker = ask_string("Ticker (or 'all' for watchlist)", default="all")

    tickers = profile.watchlist if ticker.lower() == "all" else [ticker.upper()]

    console.print("[dim]Fetching sentiment...[/]")

    table = Table(title="News Sentiment", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Ticker", style="cyan", min_width=8)
    table.add_column("Avg Score", justify="right", min_width=10)
    table.add_column("Label", min_width=12)
    table.add_column("Articles", justify="right", min_width=8)

    for t in tickers:
        result = fetch_sentiment(t, profile.alpha_vantage_key)
        if result is None:
            table.add_row(t, "[dim]N/A[/]", "[dim]No data[/]", "0")
            continue

        score = result["avg_score"]
        if score > 0.25:
            color = "green"
            label = "Bullish"
        elif score > 0.05:
            color = "green"
            label = "Somewhat Bullish"
        elif score > -0.05:
            color = "yellow"
            label = "Neutral"
        elif score > -0.25:
            color = "red"
            label = "Somewhat Bearish"
        else:
            color = "red"
            label = "Bearish"

        table.add_row(t, f"[{color}]{score:.3f}[/]", f"[{color}]{label}[/]", str(result["count"]))

    console.print(table)

    # Show latest headlines for the first ticker
    if tickers:
        result = fetch_sentiment(tickers[0], profile.alpha_vantage_key)
        if result and result["articles"]:
            console.print(f"\n[bold]Latest headlines for {tickers[0]}:[/]")
            for art in result["articles"][:3]:
                score_color = "green" if art["score"] > 0 else "red" if art["score"] < 0 else "yellow"
                console.print(f"  [{score_color}]{art['score']:+.3f}[/] {art['title']}  [dim]({art['source']})[/]")

    pause()
