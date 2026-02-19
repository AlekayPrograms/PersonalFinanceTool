"""Personal Finance CLI — Entry point and main menu loop."""

import sys
from rich.console import Console

from models.profile import UserProfile
from core.allocator import compute_allocation
from ui.display import show_dashboard, show_period_history, console as display_console
from ui.menus import show_main_menu, run_onboarding, run_settings
from ui.prompts import pause

console = Console()


def main():
    console.print("[bold cyan]Personal Finance CLI[/]", style="bold")
    console.print()

    # Load or create profile
    profile = UserProfile.load()
    if profile is None:
        profile = run_onboarding()

    # Feedback adjustments (carried across the session)
    adjustments = {}

    while True:
        try:
            choice = show_main_menu(profile)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/]")
            break

        try:
            if choice == "0":
                console.print("[dim]Goodbye![/]")
                break

            elif choice == "1":
                # Dashboard
                allocation = compute_allocation(profile, adjustments)
                show_dashboard(profile, allocation)
                pause()

            elif choice == "2":
                # Log Pay Period
                from core.feedback import log_pay_period
                adjustments = log_pay_period(profile, adjustments)

            elif choice == "3":
                # Spending History
                from models.transactions import load_records
                records = load_records()
                show_period_history(records)
                pause()

            elif choice == "4":
                # Market & Investments
                from market.stocks import market_menu
                market_menu(profile)

            elif choice == "5":
                # Retirement Tracker
                from core.retirement import retirement_menu
                retirement_menu(profile)

            elif choice == "6":
                # Debt Repayment
                from core.debt_engine import debt_menu
                debt_menu(profile)

            elif choice == "7":
                # Settings
                profile = run_settings(profile)

        except KeyboardInterrupt:
            console.print("\n[dim]Returning to menu...[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            pause()


if __name__ == "__main__":
    main()
