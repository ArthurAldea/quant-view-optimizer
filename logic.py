"""Quant-View Optimizer — Core Engine v2.0
Portfolio optimization, analytics, and backtesting using PyPortfolioOpt.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns
from pypfopt.risk_models import CovarianceShrinkage

RISK_FREE_RATE = 0.04   # 4.0% — 2026 default
LOOKBACK_YEARS = 3

STRATEGIES = {
    "Max Sharpe Ratio":  "max_sharpe",
    "Min Volatility":    "min_volatility",
    "Max Quad. Utility": "max_quadratic_utility",
}

RETURN_MODELS = {
    "Mean Historical":    "mean_historical",
    "CAPM (Market-Adj.)": "capm",
}


def fetch_prices(tickers: list[str], lookback_years: int = LOOKBACK_YEARS) -> pd.DataFrame:
    """Download adjusted close prices. Drops all-NaN ticker columns; never drops rows."""
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=lookback_years)
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]] if "Close" in raw.columns else raw
    prices = prices.dropna(axis=1, how="all")
    dropped = set(tickers) - set(prices.columns)
    if dropped:
        print(f"[warning] Dropped tickers with no data: {dropped}")
    return prices


def _compute_mu(
    prices: pd.DataFrame,
    model: str,
    rfr: float,
    lookback_years: int,
) -> tuple[pd.Series, pd.DataFrame]:
    """Return (expected_returns_series, prices_used_for_opt).
    Falls back to mean_historical if CAPM data unavailable."""
    if model == "capm":
        try:
            mkt_raw = fetch_prices(["SPY"], lookback_years)
            mkt_s   = mkt_raw.iloc[:, 0]
            common  = prices.index.intersection(mkt_s.index)
            if len(common) < 100:
                raise ValueError("Insufficient SPY overlap")
            p_aligned = prices.loc[common]
            m_aligned = mkt_s.loc[common]
            mu = expected_returns.capm_return(
                p_aligned, market_prices=m_aligned, risk_free_rate=rfr
            )
            return mu, p_aligned
        except Exception as exc:
            print(f"[CAPM fallback → mean_historical: {exc}]")
    return expected_returns.mean_historical_return(prices), prices


def asset_stats(prices: pd.DataFrame, rfr: float = RISK_FREE_RATE) -> pd.DataFrame:
    """Per-asset: annual return, volatility, Sharpe, Sortino, max drawdown."""
    rets = prices.pct_change().dropna()
    rows = []
    for ticker in prices.columns:
        r = rets[ticker].dropna()
        ann_ret = float((1 + r.mean()) ** 252 - 1)
        ann_vol = float(r.std() * np.sqrt(252))
        sharpe = (ann_ret - rfr) / ann_vol if ann_vol > 0 else 0.0
        down = r[r < 0]
        down_std = float(down.std() * np.sqrt(252)) if len(down) > 1 else ann_vol
        sortino = (ann_ret - rfr) / down_std if down_std > 0 else 0.0
        cum = (1 + r).cumprod()
        max_dd = float(((cum - cum.cummax()) / cum.cummax()).min())
        rows.append({
            "Ticker": ticker,
            "Ann. Return": ann_ret,
            "Ann. Volatility": ann_vol,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "Max Drawdown": max_dd,
        })
    return pd.DataFrame(rows).set_index("Ticker")


def optimise(
    tickers: list[str],
    strategy: str = "max_sharpe",
    rfr: float = RISK_FREE_RATE,
    lookback_years: int = LOOKBACK_YEARS,
    weight_min: float = 0.0,
    weight_max: float = 1.0,
    returns_model: str = "mean_historical",
) -> dict:
    """Run portfolio optimisation. Returns weights, performance metrics, and raw prices."""
    prices = fetch_prices(tickers, lookback_years)
    if prices.shape[1] < 2:
        raise ValueError("Need at least 2 tickers with valid data to optimise.")

    mu, prices_opt = _compute_mu(prices, returns_model, rfr, lookback_years)
    S = CovarianceShrinkage(prices_opt).ledoit_wolf()

    ef = EfficientFrontier(mu, S, weight_bounds=(weight_min, weight_max))

    if strategy == "max_sharpe":
        ef.max_sharpe(risk_free_rate=rfr)
    elif strategy == "min_volatility":
        ef.min_volatility()
    elif strategy == "max_quadratic_utility":
        ef.max_quadratic_utility(risk_aversion=1)
    else:
        ef.max_sharpe(risk_free_rate=rfr)

    weights = ef.clean_weights()
    exp_ret, ann_vol, sharpe = ef.portfolio_performance(risk_free_rate=rfr)

    # Portfolio max drawdown (use full price history for chart accuracy)
    rets = prices.pct_change().dropna()
    w_arr = np.array([weights.get(t, 0.0) for t in rets.columns])
    p_rets = rets.values @ w_arr
    cum = np.cumprod(1 + p_rets)
    peak = np.maximum.accumulate(cum)
    max_dd = float(((cum - peak) / peak).min())

    return {
        "weights": dict(weights),
        "expected_return": float(exp_ret),
        "annual_volatility": float(ann_vol),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": max_dd,
        "prices": prices,       # full history for charts/backtest
        "strategy": strategy,
        "rfr": rfr,
        "lookback": lookback_years,
        "returns_model": returns_model,
    }


def efficient_frontier(prices: pd.DataFrame, rfr: float = RISK_FREE_RATE, n: int = 40) -> dict:
    """Compute EF curve, min-vol anchor, and max-Sharpe anchor."""
    mu = expected_returns.mean_historical_return(prices)
    S = CovarianceShrinkage(prices).ledoit_wolf()

    ef_mv = EfficientFrontier(mu, S)
    ef_mv.min_volatility()
    mv_ret, mv_vol, _ = ef_mv.portfolio_performance(risk_free_rate=rfr)

    ef_ms = EfficientFrontier(mu, S)
    ef_ms.max_sharpe(risk_free_rate=rfr)
    ms_ret, ms_vol, ms_sr = ef_ms.portfolio_performance(risk_free_rate=rfr)

    max_target = float(mu.max()) * 0.98
    vols: list[float] = []
    rets_out: list[float] = []
    for t in np.linspace(float(mv_ret), max_target, n):
        try:
            ef = EfficientFrontier(mu, S)
            ef.efficient_return(t)
            r, v, _ = ef.portfolio_performance(risk_free_rate=rfr)
            rets_out.append(float(r))
            vols.append(float(v))
        except Exception:
            continue

    return {
        "vols": vols,
        "rets": rets_out,
        "min_vol": (float(mv_vol), float(mv_ret)),
        "max_sharpe": (float(ms_vol), float(ms_ret), float(ms_sr)),
    }


def backtest(
    prices: pd.DataFrame,
    weights: dict,
    benchmark: str | None = "SPY",
) -> pd.DataFrame:
    """Cumulative return backtest indexed to 100. Optionally includes a benchmark."""
    rets = prices.pct_change().dropna()
    w_arr = np.array([weights.get(t, 0.0) for t in rets.columns])
    p_rets = rets.values @ w_arr
    port = pd.Series(
        np.cumprod(1 + p_rets) * 100,
        index=rets.index,
        name="Portfolio",
    )

    if not benchmark:
        return port.to_frame()

    frames: list[pd.Series] = [port]
    try:
        start, end = rets.index[0], rets.index[-1]
        bm_raw = yf.download(benchmark, start=start, end=end, auto_adjust=True, progress=False)
        if isinstance(bm_raw.columns, pd.MultiIndex):
            bm_prices = bm_raw["Close"]
        else:
            bm_prices = bm_raw
        bm_rets = bm_prices.pct_change().dropna().reindex(rets.index).fillna(0)
        bm_cum = pd.Series(
            np.cumprod(1 + bm_rets.iloc[:, 0].values) * 100,
            index=rets.index,
            name=benchmark,
        )
        frames.append(bm_cum)
    except Exception:
        pass

    return pd.concat(frames, axis=1)


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or ["AAPL", "MSFT", "GOOGL", "AMZN"]
    print(f"Optimising: {tickers}\n")
    result = optimise(tickers)
    for t, w in result["weights"].items():
        print(f"  {t:10s} {w:.2%}")
    print(f"\nReturn:   {result['expected_return']:.2%}")
    print(f"Vol:      {result['annual_volatility']:.2%}")
    print(f"Sharpe:   {result['sharpe_ratio']:.4f}")
    print(f"Max DD:   {result['max_drawdown']:.2%}")
