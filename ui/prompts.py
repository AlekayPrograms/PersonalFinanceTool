"""Reusable input helpers for the CLI."""

from rich.console import Console
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm

console = Console()


def ask_string(prompt: str, default: str = "") -> str:
    return Prompt.ask(f"[cyan]{prompt}[/]", default=default or None) or ""


def ask_float(prompt: str, default: float = None, minimum: float = None, maximum: float = None) -> float:
    while True:
        try:
            if default is not None:
                val = FloatPrompt.ask(f"[cyan]{prompt}[/]", default=default)
            else:
                val = FloatPrompt.ask(f"[cyan]{prompt}[/]")
            if minimum is not None and val < minimum:
                console.print(f"[red]Must be at least {minimum}[/]")
                continue
            if maximum is not None and val > maximum:
                console.print(f"[red]Must be at most {maximum}[/]")
                continue
            return val
        except Exception:
            console.print("[red]Please enter a valid number.[/]")


def ask_int(prompt: str, default: int = None, minimum: int = None, maximum: int = None) -> int:
    while True:
        try:
            if default is not None:
                val = IntPrompt.ask(f"[cyan]{prompt}[/]", default=default)
            else:
                val = IntPrompt.ask(f"[cyan]{prompt}[/]")
            if minimum is not None and val < minimum:
                console.print(f"[red]Must be at least {minimum}[/]")
                continue
            if maximum is not None and val > maximum:
                console.print(f"[red]Must be at most {maximum}[/]")
                continue
            return val
        except Exception:
            console.print("[red]Please enter a valid integer.[/]")


def ask_bool(prompt: str, default: bool = False) -> bool:
    return Confirm.ask(f"[cyan]{prompt}[/]", default=default)


def ask_choice(prompt: str, choices: list[str], default: str = None) -> str:
    choices_display = " / ".join(f"[yellow]{c}[/]" for c in choices)
    while True:
        console.print(f"[cyan]{prompt}[/] ({choices_display})")
        val = Prompt.ask("Choice", default=default)
        if val in choices:
            return val
        console.print(f"[red]Invalid choice. Pick one of: {', '.join(choices)}[/]")


def ask_percentages(labels: list[str], must_sum: float = 100.0) -> list[float]:
    """Ask for a set of percentages that must sum to a target."""
    while True:
        values = []
        for label in labels:
            val = ask_float(f"  {label} %", minimum=0, maximum=must_sum)
            values.append(val)
        total = sum(values)
        if abs(total - must_sum) < 0.01:
            return values
        console.print(f"[red]Percentages must sum to {must_sum}%. Got {total:.1f}%. Try again.[/]")


def pause():
    console.print()
    Prompt.ask("[dim]Press Enter to continue[/]", default="")
