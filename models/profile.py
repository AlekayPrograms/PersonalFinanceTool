"""UserProfile dataclass with JSON persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional

from config import PROFILE_FILE, ensure_data_dir, DEFAULT_WATCHLIST


@dataclass
class UserProfile:
    name: str = ""
    gross_salary: float = 0.0
    take_home_pay: float = 0.0
    pay_frequency: str = "biweekly"  # biweekly | semimonthly | monthly | weekly

    # Budget percentages (must sum to 100)
    necessities_pct: float = 50.0
    fun_pct: float = 30.0
    savings_pct: float = 20.0

    # Savings sub-split (must sum to 100)
    savings_account_pct: float = 50.0
    investing_pct: float = 50.0

    # Debt carve-out (% of necessities allocation)
    debt_pct_of_necessities: float = 0.0

    # Retirement toggles
    roth_ira_enabled: bool = False
    roth_ira_contributed_ytd: float = 0.0
    four01k_enabled: bool = False
    # Match tiers: list of {"up_to_pct": X, "match_rate": Y}
    # e.g. [{"up_to_pct": 3, "match_rate": 100}, {"up_to_pct": 5, "match_rate": 50}]
    # means "100% match on first 3%, then 50% match on next 2%"
    four01k_match_tiers: list[dict] = field(default_factory=list)
    four01k_contribution_pct: float = 0.0  # employee contribution %
    four01k_roth: bool = False  # True = Roth 401(k), False = Before-Tax 401(k)
    four01k_contributed_ytd: float = 0.0

    # Debt toggle
    debt_enabled: bool = False

    # Market
    watchlist: list[str] = field(default_factory=lambda: list(DEFAULT_WATCHLIST))
    alpha_vantage_key: str = ""

    # Debts stored separately in transactions file
    debts: list[dict] = field(default_factory=list)

    def save(self) -> None:
        ensure_data_dir()
        with open(PROFILE_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> Optional[UserProfile]:
        try:
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    @property
    def periods_per_year(self) -> int:
        from config import PAY_FREQUENCIES
        return PAY_FREQUENCIES.get(self.pay_frequency, 26)

    @property
    def per_period_pay(self) -> float:
        return self.take_home_pay / self.periods_per_year if self.periods_per_year else 0

    @property
    def per_period_gross(self) -> float:
        return self.gross_salary / self.periods_per_year if self.periods_per_year else 0

    def compute_401k_match(self, contribution_pct: float = None) -> float:
        """Compute the employer match % based on tiers and your contribution %.

        Returns the effective match as a percentage of gross salary.
        Example: if you contribute 5% and tiers are [3%@100%, 5%@50%],
        you get 3% + 1% = 4% effective match.
        """
        if contribution_pct is None:
            contribution_pct = self.four01k_contribution_pct
        if not self.four01k_match_tiers:
            return 0.0

        match_pct = 0.0
        prev_ceiling = 0.0
        for tier in sorted(self.four01k_match_tiers, key=lambda t: t["up_to_pct"]):
            ceiling = tier["up_to_pct"]
            rate = tier["match_rate"] / 100
            # How much of this tier does the contribution cover?
            applicable = max(min(contribution_pct, ceiling) - prev_ceiling, 0)
            match_pct += applicable * rate
            prev_ceiling = ceiling
        return match_pct

    def max_match_contribution_pct(self) -> float:
        """The minimum contribution % needed to get the full employer match."""
        if not self.four01k_match_tiers:
            return 0.0
        return max(t["up_to_pct"] for t in self.four01k_match_tiers)

    def max_match_pct(self) -> float:
        """The maximum employer match % you can get (if you contribute enough)."""
        return self.compute_401k_match(self.max_match_contribution_pct())
