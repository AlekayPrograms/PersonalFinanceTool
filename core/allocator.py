"""50/30/20 budget allocation engine (customizable splits)."""

from __future__ import annotations

from dataclasses import dataclass
from models.profile import UserProfile
from config import ROTH_IRA_ANNUAL_LIMIT


@dataclass
class Allocation:
    """Single pay-period budget allocation breakdown."""
    period_pay: float

    # Top-level splits
    necessities: float
    fun: float
    savings_total: float

    # Savings sub-splits
    savings_account: float
    investing: float

    # Retirement carve-outs (from savings/investing)
    roth_ira_suggestion: float
    four01k_employee: float  # informational (pre-tax)
    four01k_employer_match: float  # informational

    # Debt carve-out (from necessities)
    debt_payment: float

    # Adjusted necessities after debt carve-out
    necessities_after_debt: float

    # Adjustments from feedback (deltas applied)
    adjustments: dict = None

    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = {}


def compute_allocation(profile: UserProfile, adjustments: dict = None) -> Allocation:
    """Compute budget allocation for one pay period.

    Args:
        profile: User profile with salary and percentage settings.
        adjustments: Optional dict of category deltas from feedback engine.
                     Keys: 'necessities', 'fun', 'savings' with float deltas.
    """
    pay = profile.per_period_pay
    if adjustments is None:
        adjustments = {}

    # Base splits
    necessities = pay * (profile.necessities_pct / 100) + adjustments.get("necessities", 0)
    fun = pay * (profile.fun_pct / 100) + adjustments.get("fun", 0)
    savings_total = pay * (profile.savings_pct / 100) + adjustments.get("savings", 0)

    # Clamp to zero
    necessities = max(necessities, 0)
    fun = max(fun, 0)
    savings_total = max(savings_total, 0)

    # Debt carve-out from necessities
    debt_payment = necessities * (profile.debt_pct_of_necessities / 100) if profile.debt_enabled else 0
    necessities_after_debt = necessities - debt_payment

    # Savings sub-split
    savings_account = savings_total * (profile.savings_account_pct / 100)
    investing = savings_total * (profile.investing_pct / 100)

    # Roth IRA suggestion (from investing portion)
    roth_suggestion = 0.0
    if profile.roth_ira_enabled:
        remaining_cap = max(ROTH_IRA_ANNUAL_LIMIT - profile.roth_ira_contributed_ytd, 0)
        periods_left = profile.periods_per_year  # simplified: spread evenly
        if periods_left > 0:
            roth_suggestion = min(remaining_cap / periods_left, investing)

    # 401k (informational — pre-tax, not deducted from take-home)
    four01k_employee = 0.0
    four01k_employer_match = 0.0
    if profile.four01k_enabled:
        four01k_employee = profile.per_period_gross * (profile.four01k_contribution_pct / 100)
        effective_match_pct = profile.compute_401k_match()
        four01k_employer_match = profile.per_period_gross * (effective_match_pct / 100)

    return Allocation(
        period_pay=pay,
        necessities=necessities,
        fun=fun,
        savings_total=savings_total,
        savings_account=savings_account,
        investing=investing,
        roth_ira_suggestion=roth_suggestion,
        four01k_employee=four01k_employee,
        four01k_employer_match=four01k_employer_match,
        debt_payment=debt_payment,
        necessities_after_debt=necessities_after_debt,
        adjustments=adjustments or {},
    )
