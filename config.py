"""Constants, file paths, and default configuration."""

import os

# Base data directory (created at runtime)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Persistence files
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
RECOMMENDATIONS_FILE = os.path.join(DATA_DIR, "recommendations.json")

# Default budget splits (50/30/20)
DEFAULT_NECESSITIES_PCT = 50
DEFAULT_FUN_PCT = 30
DEFAULT_SAVINGS_PCT = 20

# Savings sub-split (of the savings portion)
DEFAULT_SAVINGS_ACCOUNT_PCT = 50  # half to savings account
DEFAULT_INVESTING_PCT = 50        # half to investing

# Debt carved from necessities by default
DEFAULT_DEBT_PCT_OF_NECESSITIES = 0

# Retirement limits (2026)
ROTH_IRA_ANNUAL_LIMIT = 7500
DEFAULT_401K_ANNUAL_LIMIT = 23500

# Feedback damping factor (how much to correct overspending)
FEEDBACK_DAMPING = 0.50

# Market defaults
DEFAULT_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
SP500_TICKER = "^GSPC"

# Alpha Vantage
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_DAILY_LIMIT = 25

# Pay frequencies
PAY_FREQUENCIES = {
    "biweekly": 26,
    "semimonthly": 24,
    "monthly": 12,
    "weekly": 52,
}


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
