# Quant-View Optimizer

A Modern Portfolio Theory engine that computes the Max Sharpe Ratio portfolio for any set of tickers using 3 years of historical market data.

**[Live App →](https://stocksbro.streamlit.app/)**

---

## Overview

Quant-View Optimizer applies Harry Markowitz's Modern Portfolio Theory to find the optimal allocation across a user-defined basket of assets. Given a list of tickers, it fetches adjusted close prices, estimates expected returns and the covariance matrix, then solves for the portfolio that maximises the Sharpe Ratio — the highest risk-adjusted return achievable on the efficient frontier.

The result is an optimal weight per asset, with portfolio-level metrics displayed in a Bloomberg-style terminal UI.

---

## Features

- **Max Sharpe Ratio optimisation** — solves the efficient frontier using CVXPY / CLARABEL
- **Any ticker, any mix** — enter any combination of equities, ETFs, or indices supported by Yahoo Finance
- **Portfolio metrics** — Expected Annual Return, Annual Volatility, and Sharpe Ratio
- **Optimal allocation chart** — donut chart showing active position weights
- **Position breakdown table** — per-ticker weight and contribution to expected return
- **Status bar** — shows active positions, zeroed-out tickers, and solver status
- **Bloomberg-style UI** — dark terminal aesthetic with monospace typography

---

## Methodology

| Parameter | Value |
|-----------|-------|
| Data source | Yahoo Finance (yfinance) — Adjusted Close prices |
| Lookback | 3 years |
| Expected returns | Mean historical return |
| Covariance matrix | Sample covariance |
| Optimisation target | Max Sharpe Ratio |
| Risk-free rate | 4.0% (2026 default) |
| Solver | CVXPY / CLARABEL (via PyPortfolioOpt) |

Tickers with no available data are silently dropped. A minimum of 2 valid tickers is required to run the optimisation.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data | yfinance |
| Optimisation | PyPortfolioOpt (EfficientFrontier) |
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
app.py          — Streamlit dashboard and UI
logic.py        — Portfolio optimisation engine (fetch, covariance, Max Sharpe solve)
requirements.txt
```

---

## Limitations

- Expected returns are based on mean historical returns, which assume past performance is indicative of future results — they are not
- The model does not account for transaction costs, liquidity constraints, or position size limits
- Optimisation can concentrate heavily in a small number of assets; consider adding weight constraints for practical use
- Real-time prices are not used — data is fetched from Yahoo Finance at the time of running
