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
- **Ticker lookup** — search by company name to find and add tickers instantly
- **Preset watchlists** — MAG 7, S&P TOP 10, FAANG+, Dividend, Global ETF, Crypto+
- **Saved portfolios** — collapsible section; save, load, and export custom watchlists per session
- **Color-coded KPI cards** — Expected Return, Volatility, Sharpe, and Max Drawdown rendered green / amber / red based on quality thresholds
- **Weight bar chart** — horizontal bar chart companion to the allocation donut for easy magnitude comparison

### Analytics
- **Efficient frontier** — full opportunity set with Capital Market Line overlay
- **Correlation matrix** — RdBu diverging heatmap (red = positive, blue = negative correlation)
- **Risk attribution** — marginal contribution to portfolio volatility per asset
- **Monte Carlo simulation** — bootstrapped forward simulation (P10/P25/P50/P75/P90) over 1–10Y horizon with 500 / 1,000 / 5,000 paths

### Backtest
- **Historical equity curve** — portfolio vs SPY, QQQ, IWM, or BND, indexed to 100
- **Alpha calculation** — active return vs benchmark, with headline KPIs above the chart
- **Drawdown chart** — rolling peak-to-trough decline with max drawdown annotated
- **Monthly OHLC candlestick** — monthly open/high/low/close view of portfolio performance

### Holdings
- **Per-asset statistics** — annualised return, volatility, Sharpe, Sortino, max drawdown (CSV export)
- **Sharpe ratio comparison** — visual bar chart across all assets
- **Rebalancing drift** — weight drift over 1 year with BUY/SELL/HOLD signals; toggle **"Use my holdings as current weights"** to replace simulated drift with your actual portfolio fractions derived from the trade log
- **Trading history & P&L** — log trades with quantity and buy price; live current prices fetched automatically to show cost basis, current value, and unrealised P&L per position
- **Holdings-driven rebalancing** — enable the toggle after the P&L table to feed real holdings into the rebalancing engine, producing actionable BUY/SELL guidance against the optimizer's target

### Guide
- Built-in educational tab covering MPT concepts, strategies, formulas, and methodology — written for non-finance audiences

---

## UI Design

StocksBro uses a Bloomberg Terminal-inspired dark interface built entirely with custom CSS over Streamlit.

| Token | Value |
|-------|-------|
| Background | `#020c18` (near-black navy) |
| Panel | `#040f20` |
| Panel Raised | `#071628` |
| Accent | `#f5a623` (amber/gold) |
| Text | `#c8cdd4` |
| Text Muted | `#9aabb8` |
| Green | `#39d353` |
| Red | `#ff4444` |
| Font | JetBrains Mono (Google Fonts), Courier New fallback |

Key design principles:
- **Professional landing page** — hero section, 6-feature capability grid, 3-step how-it-works, engine spec row, and a styled CTA shown before any optimization is run
- **Color-coded metrics** — KPI cards use green/amber/red borders and value colors based on quality thresholds
- **Tab state persistence** — active tab is saved to localStorage and restored after Streamlit reruns (e.g. when Monte Carlo simulation parameters change)
- **Accessible contrast** — all label and body text meets WCAG AA contrast ratios against panel backgrounds
- **Keyboard-accessible tooltips** — section heading tooltips (`ⓘ`) trigger on both hover and keyboard focus
- **Responsive grids** — feature and step grids collapse to 2 columns on narrow viewports

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

Tickers with no available data are silently dropped. A minimum of 2 valid tickers is required. Weight constraints are validated before solving — if the combination of min/max weights and number of assets is mathematically infeasible, a clear error message is shown.

---

## Supported Exchanges

StocksBro pulls data from Yahoo Finance and supports any exchange it covers. Ticker format varies by exchange:

| Exchange | Suffix | Example |
|----------|--------|---------|
| US (NYSE / NASDAQ) | *(none)* | `AAPL`, `SPY` |
| ASX (Australia) | `.AX` | `CBA.AX`, `BHP.AX` |
| London Stock Exchange | `.L` | `HSBA.L` |
| Toronto Stock Exchange | `.TO` | `RY.TO` |
| Frankfurt | `.DE` | `SAP.DE` |
| Tokyo | `.T` | `7203.T` |
| Crypto (via Yahoo) | `-USD` | `BTC-USD`, `ETH-USD` |

You can mix assets from different exchanges in the same portfolio. Select your **Base Currency** in the sidebar to convert all prices into a single currency before computing returns, reducing FX distortion in the covariance matrix.

### Don't know the ticker symbol?

Use the **Ticker Lookup** field in the sidebar. Type a company name (e.g. "Apple", "BHP", "HSBC") and press **FIND** — up to 6 matching results appear showing the symbol, company name, and exchange. Press **+** to add any result directly to your ticker list.

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
app.py           — Streamlit dashboard, sidebar, session state, layout, global CSS
logic.py         — Optimisation engine (fetch, covariance, strategies, backtest, Monte Carlo)
views.py         — Tab rendering functions (Optimizer, Analytics, Backtest, Holdings)
guide.py         — Educational guide tab content
requirements.txt
```

---

## Limitations

- Expected returns are based on historical data — past performance is not indicative of future results
- The model does not account for transaction costs, liquidity constraints, or taxes
- Optimisation can concentrate heavily in a small number of assets without weight constraints
- Data is fetched from Yahoo Finance at run time — not real-time streaming prices
