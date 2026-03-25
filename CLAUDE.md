# Project: Quant-View Optimizer
A Modern Portfolio Theory (MPT) engine built with Python and Streamlit.

## Tech Stack
- Data: yfinance (3-year lookback)
- Optimization: PyPortfolioOpt (Max Sharpe Ratio)
- UI: Streamlit + Plotly
- Environment: Python 3.11+ (venv)

## Business Logic Rules
1. ALWAYS use Adjusted Close prices for returns.
2. Risk-free rate defaults to 4.0% (2026 standard).
3. Handle "None" or "NaN" ticker data by dropping columns, not rows.
4. Output must show: Weights, Annual Volatility, and Expected Return.

## Deployment Instructions
- Local: `streamlit run app.py`
- Production: Streamlit Community Cloud (via GitHub)
