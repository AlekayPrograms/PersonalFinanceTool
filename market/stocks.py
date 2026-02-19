"""yfinance wrapper for stock prices, S&P 500, and top performers."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from models.profile import UserProfile
from ui.prompts import ask_string, pause
from ui.display import fmt_money
from config import SP500_TICKER

console = Console()


def _fetch_watchlist(tickers: list[str]) -> list[dict]:
    """Fetch current prices for a list of tickers."""
    import yfinance as yf

    results = []
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev_close = info.previous_close
            change = price - prev_close if price and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            results.append({
                "ticker": ticker,
                "price": price,
                "change": change,
                "change_pct": change_pct,
            })
        except Exception:
            results.append({"ticker": ticker, "price": None, "change": 0, "change_pct": 0})
    return results


def _fetch_sp500_performance() -> dict:
    """Fetch S&P 500 recent performance."""
    import yfinance as yf

    try:
        sp = yf.Ticker(SP500_TICKER)
        hist = sp.history(period="1mo")
        if len(hist) >= 2:
            current = hist["Close"].iloc[-1]
            month_ago = hist["Close"].iloc[0]
            change = current - month_ago
            change_pct = (change / month_ago) * 100
            return {"price": current, "change": change, "change_pct": change_pct}
    except Exception:
        pass
    return {"price": None, "change": 0, "change_pct": 0}


def _show_watchlist(profile: UserProfile):
    """Display watchlist prices."""
    console.print("[dim]Fetching prices...[/]")
    data = _fetch_watchlist(profile.watchlist)

    table = Table(title="Watchlist", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Ticker", style="cyan", min_width=8)
    table.add_column("Price", justify="right", min_width=12)
    table.add_column("Change", justify="right", min_width=12)
    table.add_column("% Change", justify="right", min_width=10)

    for item in data:
        if item["price"] is None:
            table.add_row(item["ticker"], "[red]N/A[/]", "", "")
            continue

        color = "green" if item["change"] >= 0 else "red"
        sign = "+" if item["change"] >= 0 else ""
        table.add_row(
            item["ticker"],
            fmt_money(item["price"]),
            f"[{color}]{sign}{fmt_money(item['change'])}[/]",
            f"[{color}]{sign}{item['change_pct']:.2f}%[/]",
        )

    console.print(table)


def _show_sp500():
    """Display S&P 500 monthly performance."""
    console.print("[dim]Fetching S&P 500...[/]")
    data = _fetch_sp500_performance()

    if data["price"]:
        color = "green" if data["change"] >= 0 else "red"
        sign = "+" if data["change"] >= 0 else ""
        console.print(f"\n[bold]S&P 500:[/] {fmt_money(data['price'])}  "
                       f"[{color}]{sign}{fmt_money(data['change'])} ({sign}{data['change_pct']:.2f}%) 1mo[/]")
    else:
        console.print("[yellow]Could not fetch S&P 500 data.[/]")


def market_menu(profile: UserProfile):
    """Market & Investments submenu."""
    while True:
        console.print()
        console.print(Panel("[bold cyan]Market & Investments[/]", box=box.ROUNDED))
        console.print("[1] Watchlist prices")
        console.print("[2] S&P 500 performance")
        console.print("[3] News sentiment (Alpha Vantage)")
        console.print("[4] Stock recommendations")
        console.print("[0] Back")
        console.print()

        from rich.prompt import Prompt
        choice = Prompt.ask("[bold cyan]Select[/]", choices=["0", "1", "2", "3", "4"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            _show_watchlist(profile)
            pause()
        elif choice == "2":
            _show_sp500()
            pause()
        elif choice == "3":
            from market.sentiment import show_sentiment
            show_sentiment(profile)
        elif choice == "4":
            from market.recommendations import show_recommendations
            show_recommendations(profile)
