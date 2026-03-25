# StocksBro

A professional-grade Modern Portfolio Theory engine with a Bloomberg Terminal-style UI, built with Python and Streamlit.

**[Live App →](https://stocksbro.streamlit.app/)**

---

## Overview

StocksBro applies Harry Markowitz's Modern Portfolio Theory to find optimal portfolio allocations across any user-defined basket of assets. It fetches adjusted close prices, estimates expected returns and the covariance matrix (Ledoit-Wolf shrinkage), then solves for the optimal portfolio using CVXPY / CLARABEL — all presented in a dark terminal-style dashboard.

---

## Features

### Optimizer
- **3 strategies** — Max Sharpe Ratio, Min Volatility, Max Quadratic Utility
- **3 return models** — Mean Historical, CAPM, Black-Litterman
- **Configurable lookback** — 1, 2, 3, 5, or 10 years
- **Weight constraints** — min/max per position (0–25% min, 10–100% max)
- **Multi-currency** — base currency conversion support
- **Preset watchlists** — MAG 7, S&P TOP 10, FAANG+, Dividend, Global ETF, Crypto+
- **Saved portfolios** — save, load, and export custom watchlists

### Analytics
- **Efficient frontier** — full opportunity set with Capital Market Line
- **Correlation matrix** — heatmap across all assets
- **Risk attribution** — marginal contribution to portfolio volatility per asset
- **Monte Carlo simulation** — bootstrapped forward simulation (P10/P25/P50/P75/P90) over 1–10Y horizon

### Backtest
- **Historical equity curve** — portfolio vs SPY, QQQ, IWM, or BND
- **Alpha calculation** — active return vs benchmark

### Holdings
- **Per-asset statistics** — annualised return, volatility, Sharpe, Sortino, max drawdown
- **Sharpe ratio comparison** — visual bar chart across all assets
- **Rebalancing drift** — shows how weights have drifted over 1 year with BUY/SELL signals

### Guide
- Built-in educational tab covering MPT concepts, strategies, and methodology

---

## Methodology

| Parameter | Value |
|-----------|-------|
| Data source | Yahoo Finance (yfinance) — Adjusted Close prices |
| Lookback | Configurable: 1, 2, 3, 5, 10 years |
| Expected returns | Mean Historical / CAPM / Black-Litterman (user-selectable) |
| Covariance matrix | Ledoit-Wolf shrinkage |
| Optimisation targets | Max Sharpe Ratio · Min Volatility · Max Quadratic Utility |
| Risk-free rate | Configurable 0–10% (default 4.0%) |
| Solver | CVXPY / CLARABEL (via PyPortfolioOpt) |

Tickers with no available data are silently dropped. A minimum of 2 valid tickers is required.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data | yfinance |
| Optimisation | PyPortfolioOpt, CVXPY, CLARABEL |
| UI | Streamlit, Plotly |
| Runtime | Python 3.11+ |

---

## Running Locally

```bash
# 1. Clone and create a virtual environment
git clone https://github.com/ArthurAldea/quant-view-optimizer.git
cd quant-view-optimizer
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

---

## Project Structure

```
app.py          — Streamlit dashboard, sidebar, session state, layout
logic.py        — Optimisation engine (fetch, covariance, strategies, backtest, Monte Carlo)
views.py        — Tab rendering functions (Optimizer, Analytics, Backtest, Holdings)
guide.py        — Educational guide tab content
requirements.txt
```

---

## Limitations

- Expected returns are based on historical data — past performance is not indicative of future results
- The model does not account for transaction costs, liquidity constraints, or taxes
- Optimisation can concentrate heavily in a small number of assets without weight constraints
- Data is fetched from Yahoo Finance at run time — not real-time streaming prices
