"""PeriodRecord model and JSON persistence for spending history."""

from __future__ import annotations

import json
from datetime import date
from config import TRANSACTIONS_FILE, ensure_data_dir


def load_records() -> list[dict]:
    """Load all pay period records from disk."""
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_records(records: list[dict]) -> None:
    """Save all pay period records to disk."""
    ensure_data_dir()
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(records, f, indent=2)


def add_record(
    recommended_necessities: float,
    recommended_fun: float,
    recommended_savings: float,
    actual_necessities: float,
    actual_fun: float,
    actual_savings: float,
    insights: list[str] = None,
) -> dict:
    """Create a new period record, append to file, and return it."""
    record = {
        "date": date.today().isoformat(),
        "recommended_necessities": round(recommended_necessities, 2),
        "recommended_fun": round(recommended_fun, 2),
        "recommended_savings": round(recommended_savings, 2),
        "actual_necessities": round(actual_necessities, 2),
        "actual_fun": round(actual_fun, 2),
        "actual_savings": round(actual_savings, 2),
        "insights": insights or [],
    }

    records = load_records()
    records.append(record)
    save_records(records)
    return record
