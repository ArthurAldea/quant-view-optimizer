import yfinance as yf
import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns

RISK_FREE_RATE = 0.04  # 4.0% per CLAUDE.md
LOOKBACK_YEARS = 3


def fetch_prices(tickers: list[str]) -> pd.DataFrame:
    """Download adjusted close prices for the given tickers (3-year lookback).
    Drops any ticker columns with all NaN values; does not drop rows."""
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=LOOKBACK_YEARS)

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    # auto_adjust=True returns adjusted prices; select Close column
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]] if "Close" in raw.columns else raw

    # Drop columns (tickers) where all values are NaN — never drop rows
    prices = prices.dropna(axis=1, how="all")

    dropped = set(tickers) - set(prices.columns)
    if dropped:
        print(f"[warning] Dropped tickers with no data: {dropped}")

    return prices


def optimise(tickers: list[str]) -> dict:
    """Run Max Sharpe Ratio optimisation and return weights + performance metrics."""
    prices = fetch_prices(tickers)

    if prices.shape[1] < 2:
        raise ValueError("Need at least 2 tickers with valid data to optimise.")

    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)

    ef = EfficientFrontier(mu, S)
    ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
    cleaned_weights = ef.clean_weights()

    expected_return, annual_volatility, sharpe_ratio = ef.portfolio_performance(
        risk_free_rate=RISK_FREE_RATE
    )

    return {
        "weights": dict(cleaned_weights),
        "expected_return": expected_return,
        "annual_volatility": annual_volatility,
        "sharpe_ratio": sharpe_ratio,
    }


if __name__ == "__main__":
    import sys

    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["AAPL", "MSFT", "GOOGL", "AMZN"]
    print(f"Optimising portfolio for: {tickers}\n")

    result = optimise(tickers)

    print("=== Optimal Weights (Max Sharpe) ===")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker:10s} {weight:.2%}")

    print(f"\nExpected Annual Return : {result['expected_return']:.2%}")
    print(f"Annual Volatility      : {result['annual_volatility']:.2%}")
    print(f"Sharpe Ratio           : {result['sharpe_ratio']:.4f}")
