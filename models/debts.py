"""Debt dataclass and persistence (stored within profile)."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Debt:
    name: str
    balance: float
    interest_rate: float  # annual APR as percentage (e.g., 18.5)
    minimum_payment: float

    def monthly_interest(self) -> float:
        return self.balance * (self.interest_rate / 100 / 12)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Debt:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
