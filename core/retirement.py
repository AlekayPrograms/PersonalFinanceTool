"""Roth IRA + 401(k) tracking and projections."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich import box

from models.profile import UserProfile
from ui.prompts import ask_float, ask_bool, pause
from ui.display import fmt_money
from config import ROTH_IRA_ANNUAL_LIMIT, DEFAULT_401K_ANNUAL_LIMIT

console = Console()


def retirement_menu(profile: UserProfile):
    """Retirement tracker submenu."""
    if not profile.roth_ira_enabled and not profile.four01k_enabled:
        console.print()
        console.print("[yellow]No retirement accounts enabled. Enable them in Settings.[/]")
        pause()
        return

    while True:
        console.print()
        console.print(Panel("[bold cyan]Retirement Tracker[/]", box=box.ROUNDED))

        if profile.roth_ira_enabled:
            _show_roth_ira(profile)
        if profile.four01k_enabled:
            _show_401k(profile)

        console.print()
        console.print("[1] Log Roth IRA contribution" if profile.roth_ira_enabled else "", end="")
        if profile.roth_ira_enabled:
            console.print()
        console.print("[2] Log 401(k) contribution" if profile.four01k_enabled else "", end="")
        if profile.four01k_enabled:
            console.print()
        console.print("[3] Projection calculator")
        console.print("[0] Back")
        console.print()

        from rich.prompt import Prompt
        choices = ["0", "3"]
        if profile.roth_ira_enabled:
            choices.append("1")
        if profile.four01k_enabled:
            choices.append("2")
        choice = Prompt.ask("[bold cyan]Select[/]", choices=sorted(choices), default="0")

        if choice == "0":
            break
        elif choice == "1" and profile.roth_ira_enabled:
            amount = ask_float("Contribution amount", minimum=0)
            profile.roth_ira_contributed_ytd += amount
            profile.save()
            console.print(f"[green]Logged ${amount:,.2f} Roth IRA contribution.[/]")
        elif choice == "2" and profile.four01k_enabled:
            amount = ask_float("Contribution amount", minimum=0)
            profile.four01k_contributed_ytd += amount
            profile.save()
            console.print(f"[green]Logged ${amount:,.2f} 401(k) contribution.[/]")
        elif choice == "3":
            _projection_calculator(profile)


def _show_roth_ira(profile: UserProfile):
    """Display Roth IRA progress bar."""
    contributed = profile.roth_ira_contributed_ytd
    limit = ROTH_IRA_ANNUAL_LIMIT
    pct = min(contributed / limit, 1.0) if limit else 0
    remaining = max(limit - contributed, 0)

    console.print()
    console.print("[bold]Roth IRA Progress[/]")

    # Build visual progress bar
    bar_width = 40
    filled = int(pct * bar_width)
    bar = "[green]" + "█" * filled + "[/]" + "[dim]░[/]" * (bar_width - filled)

    color = "green" if pct < 0.8 else "yellow" if pct < 1.0 else "bold green"
    console.print(f"  [{color}]{bar}[/]  {pct:.1%}  ({fmt_money(contributed)} / {fmt_money(limit)})")
    console.print(f"  [dim]Remaining: {fmt_money(remaining)}[/]")

    # Per-period suggestion
    periods_left = profile.periods_per_year
    if periods_left > 0 and remaining > 0:
        per_period = remaining / periods_left
        console.print(f"  [cyan]Suggest {fmt_money(per_period)}/period to max out[/]")


def _show_401k(profile: UserProfile):
    """Display 401(k) status with tiered match breakdown."""
    contributed = profile.four01k_contributed_ytd
    limit = DEFAULT_401K_ANNUAL_LIMIT

    pct = min(contributed / limit, 1.0) if limit else 0
    remaining = max(limit - contributed, 0)

    console.print()
    console.print("[bold]401(k) Progress[/]")

    bar_width = 40
    filled = int(pct * bar_width)
    bar = "[green]" + "█" * filled + "[/]" + "[dim]░[/]" * (bar_width - filled)

    console.print(f"  {bar}  {pct:.1%}  ({fmt_money(contributed)} / {fmt_money(limit)})")
    console.print(f"  [dim]Remaining: {fmt_money(remaining)}[/]")

    # Show per-period amounts using tiered match
    per_period_employee = profile.per_period_gross * (profile.four01k_contribution_pct / 100)
    effective_match_pct = profile.compute_401k_match()
    per_period_match = profile.per_period_gross * (effective_match_pct / 100)

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Label", style="dim")
    table.add_column("Amount", style="cyan", justify="right")
    table.add_row("Your contribution/period:", fmt_money(per_period_employee))
    table.add_row(f"  ({profile.four01k_contribution_pct:.0f}% of gross)", "")
    table.add_row("Employer match/period:", fmt_money(per_period_match))
    table.add_row(f"  (effective {effective_match_pct:.1f}% of gross)", "")
    table.add_row("Total/period:", fmt_money(per_period_employee + per_period_match))
    table.add_row("Projected annual (yours):", fmt_money(per_period_employee * profile.periods_per_year))
    table.add_row("Projected annual (total):", fmt_money((per_period_employee + per_period_match) * profile.periods_per_year))
    console.print(table)

    # Show match tier breakdown so user understands where the number comes from
    if profile.four01k_match_tiers:
        console.print()
        console.print("  [bold]How your match works:[/]")
        prev = 0
        for tier in sorted(profile.four01k_match_tiers, key=lambda t: t["up_to_pct"]):
            band = f"{prev}%–{tier['up_to_pct']}%"
            covered = max(min(profile.four01k_contribution_pct, tier["up_to_pct"]) - prev, 0)
            band_match = covered * (tier["match_rate"] / 100)
            check = "[green]✓[/]" if covered > 0 else "[red]✗[/]"
            console.print(f"    {check} Your {band} → employer matches {tier['match_rate']}% "
                          f"[dim]= {band_match:.1f}% match[/]")
            prev = tier["up_to_pct"]

        # Warn if leaving money on the table
        max_needed = profile.max_match_contribution_pct()
        max_match = profile.max_match_pct()
        if profile.four01k_contribution_pct < max_needed:
            gap = max_needed - profile.four01k_contribution_pct
            lost_pct = max_match - effective_match_pct
            lost_dollars = profile.gross_salary * (lost_pct / 100)
            console.print()
            console.print(f"  [bold yellow]⚠ You're leaving {fmt_money(lost_dollars)}/year on the table![/]")
            console.print(f"  [yellow]Bump your contribution from {profile.four01k_contribution_pct:.0f}% → "
                          f"{max_needed:.0f}% to capture the full {max_match:.1f}% match.[/]")


def _projection_calculator(profile: UserProfile):
    """Simple compound growth projection."""
    console.print()
    console.print(Panel("[bold cyan]Retirement Projection Calculator[/]", box=box.ROUNDED))

    current_balance = ask_float("Current total retirement balance", minimum=0)
    annual_contribution = ask_float("Expected annual contribution", minimum=0)
    annual_return_pct = ask_float("Expected annual return %", default=7.0, minimum=0, maximum=50)
    years = int(ask_float("Years until retirement", minimum=1, maximum=60))

    rate = annual_return_pct / 100
    balance = current_balance

    table = Table(title="Projection", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Year", style="dim", justify="right")
    table.add_column("Balance", style="green", justify="right")
    table.add_column("Contributions", style="cyan", justify="right")
    table.add_column("Growth", style="yellow", justify="right")

    total_contributions = 0
    # Show every 5 years, plus final year
    for year in range(1, years + 1):
        growth = balance * rate
        balance = balance + growth + annual_contribution
        total_contributions += annual_contribution

        if year % 5 == 0 or year == years or year == 1:
            table.add_row(
                str(year),
                fmt_money(balance),
                fmt_money(total_contributions),
                fmt_money(balance - current_balance - total_contributions),
            )

    console.print(table)
    console.print()
    console.print(f"[bold green]Projected balance at retirement: {fmt_money(balance)}[/]")
    console.print(f"[dim]Total contributed: {fmt_money(total_contributions + current_balance)} | Growth: {fmt_money(balance - current_balance - total_contributions)}[/]")
    pause()
