"""Rich tables, progress bars, and formatted output."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from core.allocator import Allocation
from models.profile import UserProfile

console = Console()


def fmt_money(amount: float) -> str:
    return f"${amount:,.2f}"


def color_delta(actual: float, recommended: float) -> str:
    """Return colored string based on over/under budget."""
    delta = actual - recommended
    if abs(delta) < 0.01:
        return f"[green]{fmt_money(actual)}[/]"
    elif delta > 0:
        return f"[red]{fmt_money(actual)} (+{fmt_money(delta)})[/]"
    else:
        return f"[green]{fmt_money(actual)} ({fmt_money(delta)})[/]"


def show_dashboard(profile: UserProfile, allocation: Allocation):
    """Display the main budget dashboard."""
    console.print()
    title = f"[bold cyan]Budget Dashboard — {profile.name}[/]"
    console.print(Panel(title, box=box.DOUBLE))

    table = Table(
        title=f"Pay Period Allocation ({profile.pay_frequency.title()})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="cyan", min_width=25)
    table.add_column("Amount", justify="right", style="green", min_width=14)
    table.add_column("% of Pay", justify="right", style="yellow", min_width=10)
    table.add_column("Notes", style="dim", min_width=20)

    pay = allocation.period_pay

    def pct(val):
        return f"{(val / pay * 100):.1f}%" if pay else "0%"

    # Top-level
    table.add_row(
        "[bold]Take-Home Pay[/]",
        f"[bold]{fmt_money(pay)}[/]",
        "100%",
        f"{profile.pay_frequency.title()}",
    )
    table.add_section()

    # Necessities
    adj_note = ""
    if "necessities" in allocation.adjustments:
        d = allocation.adjustments["necessities"]
        adj_note = f"[yellow]adj {'+' if d >= 0 else ''}{fmt_money(d)}[/]"
    table.add_row("Necessities", fmt_money(allocation.necessities), pct(allocation.necessities), adj_note)

    if profile.debt_enabled and allocation.debt_payment > 0:
        table.add_row("  Debt Payment", fmt_money(allocation.debt_payment), pct(allocation.debt_payment), "from necessities")
        table.add_row("  After Debt", fmt_money(allocation.necessities_after_debt), pct(allocation.necessities_after_debt), "")

    # Fun
    adj_note = ""
    if "fun" in allocation.adjustments:
        d = allocation.adjustments["fun"]
        adj_note = f"[yellow]adj {'+' if d >= 0 else ''}{fmt_money(d)}[/]"
    table.add_row("Fun / Wants", fmt_money(allocation.fun), pct(allocation.fun), adj_note)

    # Savings
    adj_note = ""
    if "savings" in allocation.adjustments:
        d = allocation.adjustments["savings"]
        adj_note = f"[yellow]adj {'+' if d >= 0 else ''}{fmt_money(d)}[/]"
    table.add_row("Savings & Investing", fmt_money(allocation.savings_total), pct(allocation.savings_total), adj_note)
    table.add_row("  Savings Account", fmt_money(allocation.savings_account), pct(allocation.savings_account), "")
    table.add_row("  Investing", fmt_money(allocation.investing), pct(allocation.investing), "")

    # Retirement
    if profile.roth_ira_enabled:
        table.add_section()
        remaining = max(7500 - profile.roth_ira_contributed_ytd, 0)
        table.add_row(
            "Roth IRA (suggested)",
            fmt_money(allocation.roth_ira_suggestion),
            pct(allocation.roth_ira_suggestion),
            f"${remaining:,.0f} left of $7,500",
        )

    if profile.four01k_enabled:
        if not profile.roth_ira_enabled:
            table.add_section()
        roth_label = "Roth" if profile.four01k_roth else "Before-Tax"
        table.add_row(
            f"401(k) ({roth_label})",
            fmt_money(allocation.four01k_employee),
            f"{profile.four01k_contribution_pct:.1f}%",
            "[dim]pre-tax (not deducted above)[/]",
        )
        effective_match = profile.compute_401k_match()
        table.add_row(
            "401(k) Employer Match",
            fmt_money(allocation.four01k_employer_match),
            f"{effective_match:.1f}%",
            "[dim]free money! (always before-tax)[/]",
        )

    console.print(table)
    console.print()


def show_period_history(records: list[dict]):
    """Display a table of past pay periods."""
    if not records:
        console.print("[yellow]No spending history yet. Log a pay period first![/]")
        return

    table = Table(
        title="Spending History",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Date", style="cyan", min_width=12)
    table.add_column("Necessities", justify="right", min_width=20)
    table.add_column("Fun", justify="right", min_width=20)
    table.add_column("Savings", justify="right", min_width=20)
    table.add_column("Status", justify="center", min_width=10)

    for i, rec in enumerate(records, 1):
        rec_necessities = rec.get("actual_necessities", 0)
        rec_fun = rec.get("actual_fun", 0)
        rec_savings = rec.get("actual_savings", 0)
        rec_rec_n = rec.get("recommended_necessities", 0)
        rec_rec_f = rec.get("recommended_fun", 0)
        rec_rec_s = rec.get("recommended_savings", 0)

        total_actual = rec_necessities + rec_fun + rec_savings
        total_rec = rec_rec_n + rec_rec_f + rec_rec_s
        status = "[green]On Track[/]" if total_actual <= total_rec * 1.05 else "[red]Over[/]"

        table.add_row(
            str(i),
            rec.get("date", "—"),
            color_delta(rec_necessities, rec_rec_n),
            color_delta(rec_fun, rec_rec_f),
            color_delta(rec_savings, rec_rec_s),
            status,
        )

    console.print(table)
    console.print()
