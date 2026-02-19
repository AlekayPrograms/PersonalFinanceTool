"""Rule-based stock recommendations."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from models.profile import UserProfile
from ui.prompts import pause
from ui.display import fmt_money

console = Console()


def _generate_recommendations(profile: UserProfile) -> list[dict]:
    """Generate rule-based recommendations from market data."""
    import yfinance as yf
    from config import SP500_TICKER

    recs = []

    # Check S&P 500 for dip-buying opportunity
    try:
        sp = yf.Ticker(SP500_TICKER)
        hist = sp.history(period="1mo")
        if len(hist) >= 2:
            current = hist["Close"].iloc[-1]
            month_ago = hist["Close"].iloc[0]
            change_pct = ((current - month_ago) / month_ago) * 100

            if change_pct < -5:
                recs.append({
                    "type": "BUY",
                    "ticker": "SPY/VOO",
                    "reason": f"S&P 500 down {change_pct:.1f}% this month — potential buying opportunity",
                    "confidence": "Medium",
                })
            elif change_pct > 5:
                recs.append({
                    "type": "HOLD",
                    "ticker": "SPY/VOO",
                    "reason": f"S&P 500 up {change_pct:.1f}% this month — consider holding, avoid FOMO buying",
                    "confidence": "Low",
                })
    except Exception:
        pass

    # Check watchlist for opportunities
    for ticker in profile.watchlist:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="3mo")
            if len(hist) < 10:
                continue

            current = hist["Close"].iloc[-1]
            avg_3mo = hist["Close"].mean()
            high_3mo = hist["Close"].max()
            low_3mo = hist["Close"].min()

            # Near 3-month low
            if current <= low_3mo * 1.05:
                recs.append({
                    "type": "WATCH",
                    "ticker": ticker,
                    "reason": f"Near 3-month low ({fmt_money(current)} vs low {fmt_money(low_3mo)})",
                    "confidence": "Low",
                })

            # Significantly below average
            pct_below = ((avg_3mo - current) / avg_3mo) * 100
            if pct_below > 10:
                recs.append({
                    "type": "BUY",
                    "ticker": ticker,
                    "reason": f"{pct_below:.1f}% below 3-month average — may be undervalued",
                    "confidence": "Medium",
                })

            # Near 3-month high — caution
            if current >= high_3mo * 0.98:
                recs.append({
                    "type": "CAUTION",
                    "ticker": ticker,
                    "reason": f"Near 3-month high ({fmt_money(current)} vs high {fmt_money(high_3mo)})",
                    "confidence": "Low",
                })

        except Exception:
            continue

    # Sentiment-based recommendations (if API key available)
    if profile.alpha_vantage_key:
        from market.sentiment import fetch_sentiment
        for ticker in profile.watchlist[:3]:  # limit API calls
            result = fetch_sentiment(ticker, profile.alpha_vantage_key)
            if result and result["avg_score"] > 0.25:
                recs.append({
                    "type": "BULLISH",
                    "ticker": ticker,
                    "reason": f"Strong positive sentiment (score: {result['avg_score']:.3f})",
                    "confidence": "Medium",
                })
            elif result and result["avg_score"] < -0.25:
                recs.append({
                    "type": "BEARISH",
                    "ticker": ticker,
                    "reason": f"Strong negative sentiment (score: {result['avg_score']:.3f})",
                    "confidence": "Medium",
                })

    # Always add general advice
    recs.append({
        "type": "TIP",
        "ticker": "—",
        "reason": "Dollar-cost average into index funds for long-term growth",
        "confidence": "High",
    })

    return recs


def show_recommendations(profile: UserProfile):
    """Display stock recommendations."""
    console.print()
    console.print("[dim]Analyzing market data...[/]")

    recs = _generate_recommendations(profile)

    table = Table(title="Market Recommendations", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Signal", min_width=10)
    table.add_column("Ticker", style="cyan", min_width=10)
    table.add_column("Reason", min_width=40)
    table.add_column("Confidence", justify="center", min_width=10)

    type_colors = {
        "BUY": "bold green",
        "WATCH": "yellow",
        "HOLD": "cyan",
        "CAUTION": "red",
        "BULLISH": "green",
        "BEARISH": "red",
        "TIP": "dim",
    }

    for rec in recs:
        color = type_colors.get(rec["type"], "white")
        table.add_row(
            f"[{color}]{rec['type']}[/]",
            rec["ticker"],
            rec["reason"],
            rec["confidence"],
        )

    console.print(table)
    console.print()
    console.print("[dim]Disclaimer: These are rule-based signals, not financial advice. "
                   "Always do your own research.[/]")
    pause()
