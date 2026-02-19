"""Feedback engine: compares actual vs recommended, generates adjustments."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from models.profile import UserProfile
from models.transactions import add_record
from core.allocator import compute_allocation
from ui.prompts import ask_float, pause
from ui.display import fmt_money, color_delta
from config import FEEDBACK_DAMPING

console = Console()


def log_pay_period(profile: UserProfile, current_adjustments: dict) -> dict:
    """Walk user through logging a pay period and generate next-period adjustments.

    Returns updated adjustments dict for the next period.
    """
    console.print()
    console.print(Panel("[bold cyan]Log Pay Period[/]", box=box.ROUNDED))

    # Compute what was recommended this period
    allocation = compute_allocation(profile, current_adjustments)

    console.print(f"[dim]Recommended this period:[/]")
    console.print(f"  Necessities: [cyan]{fmt_money(allocation.necessities)}[/]")
    console.print(f"  Fun/Wants:   [cyan]{fmt_money(allocation.fun)}[/]")
    console.print(f"  Savings:     [cyan]{fmt_money(allocation.savings_total)}[/]")
    console.print()

    # Get actual spending
    console.print("[bold]Enter your actual spending this period:[/]")
    actual_necessities = ask_float("Necessities spent", minimum=0)
    actual_fun = ask_float("Fun/Wants spent", minimum=0)
    actual_savings = ask_float("Amount saved/invested", minimum=0)

    # Compute deltas
    delta_n = actual_necessities - allocation.necessities
    delta_f = actual_fun - allocation.fun
    delta_s = actual_savings - allocation.savings_total

    # Generate insights
    insights = []
    categories = [
        ("Necessities", delta_n, allocation.necessities),
        ("Fun/Wants", delta_f, allocation.fun),
        ("Savings", delta_s, allocation.savings_total),
    ]

    for name, delta, recommended in categories:
        if recommended == 0:
            continue
        pct = (delta / recommended) * 100
        if abs(pct) < 2:
            insights.append(f"{name}: Right on target!")
        elif delta > 0:
            insights.append(f"{name}: Overspent by {fmt_money(delta)} ({pct:+.1f}%)")
        else:
            insights.append(f"{name}: Under budget by {fmt_money(-delta)} ({pct:+.1f}%)")

    # Display results
    console.print()
    table = Table(title="Period Summary", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Category", style="cyan", min_width=15)
    table.add_column("Recommended", justify="right", min_width=12)
    table.add_column("Actual", justify="right", min_width=18)
    table.add_column("Delta", justify="right", min_width=14)

    def delta_str(d):
        if d > 0.01:
            return f"[red]+{fmt_money(d)}[/]"
        elif d < -0.01:
            return f"[green]{fmt_money(d)}[/]"
        return "[green]$0.00[/]"

    table.add_row("Necessities", fmt_money(allocation.necessities),
                   color_delta(actual_necessities, allocation.necessities),
                   delta_str(delta_n))
    table.add_row("Fun/Wants", fmt_money(allocation.fun),
                   color_delta(actual_fun, allocation.fun),
                   delta_str(delta_f))
    table.add_row("Savings", fmt_money(allocation.savings_total),
                   color_delta(actual_savings, allocation.savings_total),
                   delta_str(delta_s))

    console.print(table)

    # Insights
    console.print()
    console.print("[bold]Insights:[/]")
    for insight in insights:
        console.print(f"  {insight}")

    # Compute next-period adjustments (50% damped correction)
    new_adjustments = {}

    # Overspent categories get reduced next period
    if delta_n > 0:
        new_adjustments["necessities"] = -delta_n * FEEDBACK_DAMPING
    if delta_f > 0:
        new_adjustments["fun"] = -delta_f * FEEDBACK_DAMPING

    # Freed-up money from reductions goes to savings priority
    freed = sum(-v for v in new_adjustments.values() if v < 0)
    if freed > 0:
        new_adjustments["savings"] = freed

    # Under-spent savings gets kept (positive reinforcement)
    if delta_s < 0:
        # Saved less than recommended — no penalty, just note it
        insights.append("Consider increasing savings next period.")

    if new_adjustments:
        console.print()
        console.print("[bold yellow]Next Period Adjustments:[/]")
        for cat, adj in new_adjustments.items():
            direction = "increase" if adj > 0 else "decrease"
            console.print(f"  {cat.title()}: {direction} by {fmt_money(abs(adj))}")

    # Save record
    add_record(
        recommended_necessities=allocation.necessities,
        recommended_fun=allocation.fun,
        recommended_savings=allocation.savings_total,
        actual_necessities=actual_necessities,
        actual_fun=actual_fun,
        actual_savings=actual_savings,
        insights=insights,
    )

    console.print()
    console.print("[green]Pay period logged![/]")
    pause()

    return new_adjustments
