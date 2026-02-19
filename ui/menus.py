"""Menu flow, onboarding wizard, and input handling."""

from rich.console import Console
from rich.panel import Panel
from rich import box

from models.profile import UserProfile
from ui.prompts import (
    ask_string, ask_float, ask_bool, ask_choice, ask_percentages, pause, console as prompt_console,
)
from config import PAY_FREQUENCIES

console = Console()


def _setup_401k_match(profile: UserProfile):
    """Friendly employer match setup using common presets."""
    from ui.display import fmt_money

    console.print()
    console.print("[bold]Employer Match Setup[/]")
    console.print("[dim]Pick the option that matches your company's policy.[/]")
    console.print("[dim]Don't worry — you can always change this later in Settings.[/]")
    console.print()
    console.print("[1] [cyan]100% of first 3%, then 50% of next 2%[/]")
    console.print("    [dim]Most common plan. Contribute 5% → get 4% match.[/]")
    console.print("[2] [cyan]100% match up to a limit[/]")
    console.print("    [dim]Dollar-for-dollar up to X%. Contribute X% → get X% match.[/]")
    console.print("[3] [cyan]50% match up to a limit[/]")
    console.print("    [dim]Fifty cents per dollar up to X%. Contribute X% → get X/2% match.[/]")
    console.print("[4] [cyan]Custom / my plan is different[/]")
    console.print("    [dim]Enter your own tiers step by step.[/]")
    console.print("[5] [cyan]No employer match[/]")
    console.print("    [dim]Your employer doesn't match contributions.[/]")
    console.print()

    from rich.prompt import Prompt
    choice = Prompt.ask("[bold cyan]Select[/]", choices=["1", "2", "3", "4", "5"], default="1")

    if choice == "1":
        # Most common: 100% up to 3%, 50% up to 5%
        profile.four01k_match_tiers = [
            {"up_to_pct": 3, "match_rate": 100},
            {"up_to_pct": 5, "match_rate": 50},
        ]
    elif choice == "2":
        limit = ask_float("Employer matches 100% up to what %?", default=3, minimum=0, maximum=100)
        profile.four01k_match_tiers = [
            {"up_to_pct": limit, "match_rate": 100},
        ]
    elif choice == "3":
        limit = ask_float("Employer matches 50% up to what %?", default=6, minimum=0, maximum=100)
        profile.four01k_match_tiers = [
            {"up_to_pct": limit, "match_rate": 50},
        ]
    elif choice == "4":
        _custom_match_tiers(profile)
    elif choice == "5":
        profile.four01k_match_tiers = []

    # Show summary so they know what they picked
    if profile.four01k_match_tiers:
        effective = profile.compute_401k_match()
        max_needed = profile.max_match_contribution_pct()
        max_match = profile.max_match_pct()
        annual_match = profile.gross_salary * (effective / 100)
        max_annual = profile.gross_salary * (max_match / 100)

        console.print()
        console.print("[bold green]Here's what that means for you:[/]")
        console.print(f"  You contribute [cyan]{profile.four01k_contribution_pct:.0f}%[/] → "
                       f"employer adds [green]{effective:.1f}%[/] → "
                       f"[green]{fmt_money(annual_match)}/year free money[/]")

        if profile.four01k_contribution_pct < max_needed:
            console.print()
            console.print(f"  [yellow]Tip: If you bump to {max_needed:.0f}%, you'd get the full "
                           f"{max_match:.1f}% match ({fmt_money(max_annual)}/year).[/]")
        elif profile.four01k_contribution_pct >= max_needed:
            console.print(f"  [green]You're getting the full match![/]")


def _custom_match_tiers(profile: UserProfile):
    """Walk through adding custom match tiers one at a time."""
    console.print()
    console.print("[bold]Custom Match Tiers[/]")
    console.print("[dim]Enter each tier of your employer's match formula.[/]")
    console.print("[dim]Example: if your plan says '100% up to 3%, then 50% from 3-5%',[/]")
    console.print("[dim]you'd add two tiers: tier 1 = up to 3% at 100%, tier 2 = up to 5% at 50%.[/]")
    console.print()

    tiers = []
    while True:
        tier_num = len(tiers) + 1
        console.print(f"[bold]Tier {tier_num}:[/]")
        up_to = ask_float("  Employer matches up to what % of your salary?", minimum=0, maximum=100)
        rate = ask_float("  At what match rate? (e.g., 100 = dollar-for-dollar, 50 = fifty cents per dollar)", minimum=0, maximum=100)

        tiers.append({"up_to_pct": up_to, "match_rate": rate})

        # Quick preview
        prev = 0
        for t in sorted(tiers, key=lambda x: x["up_to_pct"]):
            console.print(f"    [dim]{prev}%–{t['up_to_pct']}% of salary → {t['match_rate']}% match[/]")
            prev = t["up_to_pct"]

        if not ask_bool("Add another tier?", default=False):
            break

    profile.four01k_match_tiers = tiers


def show_main_menu(profile: UserProfile) -> str:
    console.print()
    console.print(Panel(
        "[bold cyan]Personal Finance CLI[/]\n"
        f"[dim]{profile.name} | {profile.pay_frequency.title()} | Take-home: ${profile.take_home_pay:,.2f}/yr[/]",
        box=box.DOUBLE,
    ))
    console.print("[1] Dashboard")
    console.print("[2] Log Pay Period")
    console.print("[3] Spending History")
    console.print("[4] Market & Investments")
    console.print("[5] Retirement Tracker")
    console.print("[6] Debt Repayment")
    console.print("[7] Settings")
    console.print("[0] Exit")
    console.print()

    from rich.prompt import Prompt
    return Prompt.ask("[bold cyan]Select[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")


def run_onboarding() -> UserProfile:
    """First-run onboarding wizard."""
    console.print()
    console.print(Panel("[bold green]Welcome to Personal Finance CLI![/]\nLet's set up your profile.", box=box.DOUBLE))
    console.print()

    profile = UserProfile()

    # Basic info
    profile.name = ask_string("Your name")
    profile.gross_salary = ask_float("Annual gross salary", minimum=0)
    profile.take_home_pay = ask_float("Annual take-home pay (after taxes)", minimum=0)
    profile.pay_frequency = ask_choice(
        "Pay frequency",
        list(PAY_FREQUENCIES.keys()),
        default="biweekly",
    )

    # Budget split
    console.print()
    console.print("[bold]Budget Split[/]")
    use_default = ask_bool("Use default 50/30/20 split?", default=True)
    if use_default:
        profile.necessities_pct = 50
        profile.fun_pct = 30
        profile.savings_pct = 20
    else:
        console.print("[dim]Enter percentages for each category (must sum to 100%):[/]")
        pcts = ask_percentages(["Necessities", "Fun/Wants", "Savings & Investing"])
        profile.necessities_pct, profile.fun_pct, profile.savings_pct = pcts

    # Savings sub-split
    console.print()
    console.print("[bold]Savings Breakdown[/]")
    use_default_savings = ask_bool("Split savings 50/50 between savings account and investing?", default=True)
    if not use_default_savings:
        pcts = ask_percentages(["Savings Account", "Investing"])
        profile.savings_account_pct, profile.investing_pct = pcts

    # Retirement
    console.print()
    console.print("[bold]Retirement[/]")
    profile.roth_ira_enabled = ask_bool("Track Roth IRA contributions?", default=False)
    if profile.roth_ira_enabled:
        profile.roth_ira_contributed_ytd = ask_float("Roth IRA contributed so far this year", default=0, minimum=0)

    profile.four01k_enabled = ask_bool("Track 401(k)?", default=False)
    if profile.four01k_enabled:
        profile.four01k_contribution_pct = ask_float("Your 401(k) contribution %", default=6, minimum=0, maximum=90)
        _setup_401k_match(profile)

    # Debt
    console.print()
    profile.debt_enabled = ask_bool("Enable debt repayment tracking?", default=False)
    if profile.debt_enabled:
        profile.debt_pct_of_necessities = ask_float(
            "% of necessities to allocate to debt payments",
            default=10, minimum=0, maximum=100,
        )

    profile.save()
    console.print()
    console.print("[bold green]Profile saved! You're all set.[/]")
    pause()
    return profile


def run_settings(profile: UserProfile) -> UserProfile:
    """Settings submenu."""
    while True:
        console.print()
        console.print(Panel("[bold cyan]Settings[/]", box=box.ROUNDED))
        console.print("[1] Edit profile (name, salary)")
        console.print("[2] Edit budget percentages")
        console.print("[3] Edit savings sub-split")
        console.print("[4] Retirement toggles")
        console.print("[5] Debt toggle")
        console.print("[6] Stock watchlist")
        console.print("[7] Alpha Vantage API key")
        console.print("[0] Back")
        console.print()

        from rich.prompt import Prompt
        choice = Prompt.ask("[bold cyan]Select[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            profile.name = ask_string("Name", default=profile.name)
            profile.gross_salary = ask_float("Annual gross salary", default=profile.gross_salary, minimum=0)
            profile.take_home_pay = ask_float("Annual take-home pay", default=profile.take_home_pay, minimum=0)
            profile.pay_frequency = ask_choice(
                "Pay frequency", list(PAY_FREQUENCIES.keys()), default=profile.pay_frequency,
            )
        elif choice == "2":
            console.print(f"[dim]Current: {profile.necessities_pct}/{profile.fun_pct}/{profile.savings_pct}[/]")
            pcts = ask_percentages(["Necessities", "Fun/Wants", "Savings & Investing"])
            profile.necessities_pct, profile.fun_pct, profile.savings_pct = pcts
        elif choice == "3":
            console.print(f"[dim]Current: {profile.savings_account_pct}% savings / {profile.investing_pct}% investing[/]")
            pcts = ask_percentages(["Savings Account", "Investing"])
            profile.savings_account_pct, profile.investing_pct = pcts
        elif choice == "4":
            profile.roth_ira_enabled = ask_bool("Track Roth IRA?", default=profile.roth_ira_enabled)
            if profile.roth_ira_enabled:
                profile.roth_ira_contributed_ytd = ask_float(
                    "Roth IRA contributed YTD", default=profile.roth_ira_contributed_ytd, minimum=0,
                )
            profile.four01k_enabled = ask_bool("Track 401(k)?", default=profile.four01k_enabled)
            if profile.four01k_enabled:
                profile.four01k_contribution_pct = ask_float(
                    "Your 401(k) contribution %", default=profile.four01k_contribution_pct, minimum=0, maximum=90,
                )
                reconfigure = ask_bool("Reconfigure employer match?", default=False)
                if reconfigure:
                    _setup_401k_match(profile)
        elif choice == "5":
            profile.debt_enabled = ask_bool("Enable debt repayment?", default=profile.debt_enabled)
            if profile.debt_enabled:
                profile.debt_pct_of_necessities = ask_float(
                    "% of necessities for debt", default=profile.debt_pct_of_necessities, minimum=0, maximum=100,
                )
        elif choice == "6":
            console.print(f"[dim]Current watchlist: {', '.join(profile.watchlist)}[/]")
            action = ask_choice("Action", ["add", "remove", "replace"], default="add")
            if action == "add":
                ticker = ask_string("Ticker to add").upper()
                if ticker and ticker not in profile.watchlist:
                    profile.watchlist.append(ticker)
            elif action == "remove":
                ticker = ask_string("Ticker to remove").upper()
                if ticker in profile.watchlist:
                    profile.watchlist.remove(ticker)
            elif action == "replace":
                tickers = ask_string("New watchlist (comma-separated)").upper()
                profile.watchlist = [t.strip() for t in tickers.split(",") if t.strip()]
        elif choice == "7":
            profile.alpha_vantage_key = ask_string("Alpha Vantage API key", default=profile.alpha_vantage_key)

        profile.save()
        console.print("[green]Settings saved.[/]")

    return profile
