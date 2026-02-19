"""Avalanche/snowball debt repayment calculator."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from models.profile import UserProfile
from models.debts import Debt
from ui.prompts import ask_float, ask_string, ask_choice, pause
from ui.display import fmt_money

console = Console()


def debt_menu(profile: UserProfile):
    """Debt repayment submenu."""
    if not profile.debt_enabled:
        console.print()
        console.print("[yellow]Debt module is disabled. Enable it in Settings.[/]")
        pause()
        return

    while True:
        console.print()
        console.print(Panel("[bold cyan]Debt Repayment[/]", box=box.ROUNDED))

        debts = [Debt.from_dict(d) for d in profile.debts]

        if debts:
            _show_debts_table(debts)
        else:
            console.print("[dim]No debts tracked yet.[/]")

        console.print()
        console.print("[1] Add a debt")
        console.print("[2] Remove a debt")
        console.print("[3] Repayment plan (avalanche)")
        console.print("[4] Repayment plan (snowball)")
        console.print("[5] Log a payment")
        console.print("[0] Back")
        console.print()

        from rich.prompt import Prompt
        choice = Prompt.ask("[bold cyan]Select[/]", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            _add_debt(profile)
        elif choice == "2":
            _remove_debt(profile)
        elif choice == "3":
            _repayment_plan(profile, method="avalanche")
        elif choice == "4":
            _repayment_plan(profile, method="snowball")
        elif choice == "5":
            _log_payment(profile)


def _show_debts_table(debts: list[Debt]):
    """Display current debts."""
    table = Table(title="Current Debts", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan", min_width=20)
    table.add_column("Balance", justify="right", style="red", min_width=12)
    table.add_column("APR", justify="right", style="yellow", min_width=8)
    table.add_column("Min Payment", justify="right", style="green", min_width=12)
    table.add_column("Monthly Interest", justify="right", style="red", min_width=14)

    total_balance = 0
    total_min = 0
    for i, d in enumerate(debts, 1):
        table.add_row(
            str(i), d.name, fmt_money(d.balance),
            f"{d.interest_rate:.1f}%", fmt_money(d.minimum_payment),
            fmt_money(d.monthly_interest()),
        )
        total_balance += d.balance
        total_min += d.minimum_payment

    table.add_section()
    table.add_row("", "[bold]Total[/]", f"[bold red]{fmt_money(total_balance)}[/]", "",
                   f"[bold]{fmt_money(total_min)}[/]", "")

    console.print(table)


def _add_debt(profile: UserProfile):
    """Add a new debt."""
    name = ask_string("Debt name (e.g., 'Chase Visa')")
    balance = ask_float("Current balance", minimum=0)
    rate = ask_float("Annual interest rate %", minimum=0, maximum=100)
    min_pay = ask_float("Minimum monthly payment", minimum=0)

    debt = Debt(name=name, balance=balance, interest_rate=rate, minimum_payment=min_pay)
    profile.debts.append(debt.to_dict())
    profile.save()
    console.print(f"[green]Added {name}.[/]")


def _remove_debt(profile: UserProfile):
    """Remove a debt by index."""
    if not profile.debts:
        console.print("[yellow]No debts to remove.[/]")
        return
    for i, d in enumerate(profile.debts, 1):
        console.print(f"  [{i}] {d['name']} — {fmt_money(d['balance'])}")
    idx = int(ask_float("Debt # to remove", minimum=1, maximum=len(profile.debts))) - 1
    removed = profile.debts.pop(idx)
    profile.save()
    console.print(f"[green]Removed {removed['name']}.[/]")


def _log_payment(profile: UserProfile):
    """Log a payment against a debt."""
    if not profile.debts:
        console.print("[yellow]No debts to pay.[/]")
        return
    for i, d in enumerate(profile.debts, 1):
        console.print(f"  [{i}] {d['name']} — {fmt_money(d['balance'])}")
    idx = int(ask_float("Debt # to pay", minimum=1, maximum=len(profile.debts))) - 1
    amount = ask_float("Payment amount", minimum=0)
    profile.debts[idx]["balance"] = max(profile.debts[idx]["balance"] - amount, 0)
    profile.save()
    console.print(f"[green]Paid {fmt_money(amount)} toward {profile.debts[idx]['name']}. "
                   f"New balance: {fmt_money(profile.debts[idx]['balance'])}[/]")


def _repayment_plan(profile: UserProfile, method: str = "avalanche"):
    """Generate a repayment schedule using avalanche or snowball method."""
    if not profile.debts:
        console.print("[yellow]No debts to plan.[/]")
        pause()
        return

    extra = ask_float("Extra monthly payment beyond minimums", default=0, minimum=0)

    debts = [Debt.from_dict(d) for d in profile.debts]
    total_min = sum(d.minimum_payment for d in debts)
    monthly_budget = total_min + extra

    console.print()
    console.print(f"[bold]Repayment Plan ({method.title()} Method)[/]")
    console.print(f"[dim]Monthly budget: {fmt_money(monthly_budget)} (minimums {fmt_money(total_min)} + extra {fmt_money(extra)})[/]")
    console.print()

    # Simulate payoff
    balances = [d.balance for d in debts]
    rates = [d.interest_rate / 100 / 12 for d in debts]
    mins = [d.minimum_payment for d in debts]
    names = [d.name for d in debts]

    month = 0
    total_interest = 0
    payoff_months = [0] * len(debts)
    max_months = 360  # 30-year cap

    table = Table(title=f"{method.title()} Schedule", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Month", style="dim", justify="right", width=6)
    for name in names:
        table.add_column(name, justify="right", min_width=12)
    table.add_column("Total", justify="right", style="bold", min_width=12)

    while any(b > 0.01 for b in balances) and month < max_months:
        month += 1

        # Apply interest
        for i in range(len(debts)):
            if balances[i] > 0:
                interest = balances[i] * rates[i]
                balances[i] += interest
                total_interest += interest

        # Pay minimums
        remaining_budget = monthly_budget
        for i in range(len(debts)):
            if balances[i] > 0:
                payment = min(mins[i], balances[i], remaining_budget)
                balances[i] -= payment
                remaining_budget -= payment

        # Apply extra to target debt
        if remaining_budget > 0:
            if method == "avalanche":
                # Highest interest first
                order = sorted(range(len(debts)), key=lambda i: rates[i], reverse=True)
            else:
                # Lowest balance first
                order = sorted(range(len(debts)), key=lambda i: balances[i])

            for i in order:
                if balances[i] > 0 and remaining_budget > 0:
                    payment = min(balances[i], remaining_budget)
                    balances[i] -= payment
                    remaining_budget -= payment

        # Record payoff months
        for i in range(len(debts)):
            if balances[i] <= 0.01 and payoff_months[i] == 0:
                payoff_months[i] = month

        # Show every 3 months or final
        if month % 3 == 0 or all(b <= 0.01 for b in balances):
            row = [str(month)]
            for b in balances:
                row.append(fmt_money(max(b, 0)))
            row.append(fmt_money(sum(max(b, 0) for b in balances)))
            table.add_row(*row)

    console.print(table)
    console.print()

    # Summary
    console.print("[bold]Payoff Summary:[/]")
    for i, name in enumerate(names):
        if payoff_months[i]:
            years = payoff_months[i] // 12
            months = payoff_months[i] % 12
            time_str = f"{years}y {months}m" if years else f"{months}m"
            console.print(f"  {name}: paid off in [green]{time_str}[/]")
        else:
            console.print(f"  {name}: [red]not paid off within 30 years[/]")

    console.print(f"\n  Total interest paid: [red]{fmt_money(total_interest)}[/]")
    if month < max_months:
        years = month // 12
        months = month % 12
        console.print(f"  Debt-free in: [bold green]{years}y {months}m[/]")
    pause()
