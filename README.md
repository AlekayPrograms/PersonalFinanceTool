# PersonalFinance

## About This Project

Growing up in an immigrant family, financial literacy wasn't something that was taught - it was something I had to piece together on my own, often making costly mistakes along the way. Watching my family navigate a system that felt entirely foreign, with no safety net of inherited knowledge, sparked a deep interest in understanding money and how it works. I built this tool for people like us - those who weren't handed a financial roadmap and had to figure it out the hard way. My hope is that it makes managing personal finances a little more accessible, a little less intimidating, and a lot more empowering.


According to the [GFLEC Personal Finance Index (2024)](https://gflec.org/initiatives/personal-finance-index/), financial literacy in the US has stagnated around 50% for eight consecutive years, with a 2% drop over the past two years - meaning roughly half of Americans still lack the foundational knowledge to make informed financial decisions. That number represents millions of real people struggling with debt, savings, and retirement planning without the tools to navigate it. This project is my small contribution toward closing that gap, built with the belief that financial education shouldn't be a privilege. If this tool helps even one person feel more in control of their finances, it's worth it.

## Features

### Dashboard & Budget Allocation
Automatically splits your take-home pay using the **50/30/20 rule** - 50% necessities, 30% fun/wants, 20% savings - with full customization. Savings are further split between a savings account and investing. After each pay period, the app compares what you actually spent to what was recommended and adjusts the next period's budget automatically (with a 50% damping factor so corrections are gradual, not jarring).

### Pay Period Logging & Spending History
Log your actual spending each pay period across three categories (necessities, fun, savings). The app tells you exactly how much you were over or under in each category, saves a full history of every period, and uses that data to refine future recommendations.

### Market & Investments
Tracks a customizable stock watchlist - defaults to **AAPL, MSFT, GOOGL, AMZN, and NVDA** - with live prices and daily change pulled via `yfinance`. Also tracks the **S&P 500 (^GSPC)** monthly performance. Includes a rule-based recommendation engine that flags dip-buying opportunities (S&P 500 down >5% in a month), stocks near their 3-month low, stocks trading >10% below their 3-month average, and caution signals when stocks are near their 3-month high. Optional **Alpha Vantage** API integration adds news sentiment scores to strengthen or weaken those signals.

> **⚠️ Limitation - the market signals are elementary.** The recommendation engine is rule-based and intentionally simple - it is not grounded in serious investment theory. It has no technical indicators (no RSI, MACD, or moving average crossovers), no fundamental analysis (no P/E ratios, earnings growth, or valuation metrics), no risk metrics (no beta, Sharpe ratio, or volatility), and no portfolio theory (no position sizing, correlation, or diversification analysis). "Near 3-month low" is not a real buy signal on its own - a stock can be in freefall and keep falling. The only genuinely evidence-backed advice the app gives is to dollar-cost average into broad index funds. **Treat all other signals as a starting point for your own research, not as financial advice.**

### Retirement Tracker
Tracks progress toward the **2026 Roth IRA limit ($7,500)** and **401(k) limit ($23,500)** with visual progress bars. Supports tiered employer match configurations (e.g., 100% of first 3%, 50% of next 2%) and warns you if you're leaving free employer match money on the table. Includes a compound growth projection calculator - enter your current balance, annual contribution, expected return, and years to retirement.

### Debt Repayment
Supports multiple debts simultaneously. Generates month-by-month repayment schedules using either the **avalanche method** (highest interest first - minimizes total interest paid) or the **snowball method** (lowest balance first - builds momentum). Shows total interest paid and time to debt-free for each method so you can compare.

### Onboarding & Settings
First-run wizard walks you through salary, pay frequency (weekly, biweekly, semimonthly, monthly), budget splits, retirement accounts, employer match setup, and debt tracking. Everything is editable later from the Settings menu, including your watchlist and API keys.

## Getting Started

```bash
pip install -r requirements.txt
python main.py
```
