"""Quant-View Optimizer — Core Engine v2.2
Portfolio optimization, analytics, and backtesting using PyPortfolioOpt.
"""
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns
from pypfopt.risk_models import CovarianceShrinkage
from pypfopt import black_litterman as bl_utils
from pypfopt.black_litterman import BlackLittermanModel

RISK_FREE_RATE = 0.04   # 4.0% — 2026 default
LOOKBACK_YEARS = 10

STRATEGIES = {
    "Max Sharpe Ratio":  "max_sharpe",
    "Min Volatility":    "min_volatility",
    "Max Quad. Utility": "max_quadratic_utility",
}

RETURN_MODELS = {
    "Mean Historical":    "mean_historical",
    "CAPM (Market-Adj.)": "capm",
    "Black-Litterman":    "black_litterman",
}

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]


def fetch_prices(
    tickers: list[str],
    lookback_years: int = LOOKBACK_YEARS,
    base_currency: str = "USD",
) -> pd.DataFrame:
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

    if base_currency != "USD":
        try:
            fx_pair = f"USD{base_currency}=X"
            fx_raw = yf.download(fx_pair, start=start, end=end, auto_adjust=True, progress=False)
            if isinstance(fx_raw.columns, pd.MultiIndex):
                fx = fx_raw["Close"].iloc[:, 0]
            elif "Close" in fx_raw.columns:
                fx = fx_raw["Close"]
            else:
                fx = fx_raw.iloc[:, 0]
            fx = fx.reindex(prices.index).ffill().bfill()
            prices = prices.multiply(fx, axis=0)
        except Exception as exc:
            print(f"[FX conversion failed for {base_currency}: {exc}]")

    return prices


def search_tickers(query: str) -> list[dict]:
    """Search Yahoo Finance for tickers matching a company name or symbol.
    Returns a list of dicts with keys: symbol, name, exchange, type.
    """
    try:
        resp = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": 6, "newsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        resp.raise_for_status()
        results = []
        for q in resp.json().get("quotes", []):
            symbol = q.get("symbol", "")
            if not symbol:
                continue
            results.append({
                "symbol":   symbol,
                "name":     q.get("shortname") or q.get("longname") or "",
                "exchange": q.get("exchDisp") or q.get("exchange") or "",
                "type":     q.get("typeDisp") or q.get("quoteType") or "",
            })
        return results
    except Exception:
        return []


def get_company_names(tickers: list[str]) -> dict[str, str]:
    """Fetch company short names via yfinance. Falls back to ticker symbol on error."""
    names: dict[str, str] = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            names[t] = info.get("shortName") or info.get("longName") or t
        except Exception:
            names[t] = t
    return names


def _compute_mu(
    prices: pd.DataFrame,
    model: str,
    rfr: float,
    lookback_years: int,
) -> tuple[pd.Series, pd.DataFrame]:
    """Return (expected_returns_series, prices_used_for_opt).
    Falls back to mean_historical if preferred model data is unavailable."""
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

    elif model == "black_litterman":
        try:
            mcaps: dict[str, float] = {}
            for t in prices.columns:
                try:
                    mc = yf.Ticker(t).fast_info.market_cap
                    if mc and float(mc) > 0:
                        mcaps[t] = float(mc)
                except Exception:
                    pass
            if len(mcaps) < 2:
                raise ValueError("Insufficient market cap data for BL")

            spy_raw = fetch_prices(["SPY"], lookback_years)
            spy_prices = spy_raw.iloc[:, 0]
            valid_tks = [t for t in prices.columns if t in mcaps]
            p_bl = prices[valid_tks]
            common = p_bl.index.intersection(spy_prices.index)
            if len(common) < 100:
                raise ValueError("Insufficient overlap for BL")
            p_bl = p_bl.loc[common]
            spy_aligned = spy_prices.loc[common]

            S_bl = CovarianceShrinkage(p_bl).ledoit_wolf()
            delta = bl_utils.market_implied_risk_aversion(spy_aligned, risk_free_rate=rfr)
            mcaps_valid = {t: mcaps[t] for t in valid_tks}
            prior = bl_utils.market_implied_prior_returns(mcaps_valid, delta, S_bl)
            blm = BlackLittermanModel(S_bl, pi=prior)
            mu = blm.bl_returns()
            return mu, p_bl
        except Exception as exc:
            print(f"[BL fallback → mean_historical: {exc}]")

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
    base_currency: str = "USD",
) -> dict:
    """Run portfolio optimisation. Returns weights, performance metrics, and raw prices."""
    prices = fetch_prices(tickers, lookback_years, base_currency)
    if prices.shape[1] < 2:
        raise ValueError("Need at least 2 tickers with valid data to optimise.")

    mu, prices_opt = _compute_mu(prices, returns_model, rfr, lookback_years)
    S = CovarianceShrinkage(prices_opt).ledoit_wolf()

    n_assets = len(mu)
    if weight_max * n_assets < 1.0 - 1e-9:
        raise ValueError(
            f"Infeasible constraints: {n_assets} assets × max {weight_max:.0%}/position = "
            f"{n_assets * weight_max:.0%} < 100%. "
            f"Raise max per position to at least {100 / n_assets:.0f}%."
        )
    if weight_min * n_assets > 1.0 + 1e-9:
        raise ValueError(
            f"Infeasible constraints: {n_assets} assets × min {weight_min:.0%}/position = "
            f"{n_assets * weight_min:.0%} > 100%. "
            f"Lower min per position to at most {100 / n_assets:.0f}%."
        )

    ef = EfficientFrontier(mu, S, weight_bounds=(weight_min, weight_max))
    if strategy == "max_sharpe":
        ef.max_sharpe(risk_free_rate=rfr)
    elif strategy == "min_volatility":
        ef.min_volatility()
    elif strategy == "max_quadratic_utility":
        ef.max_quadratic_utility(risk_aversion=1)
    else:
        ef.max_sharpe(risk_free_rate=rfr)

    # Cutoff below weight_min so constrained weights aren't zeroed and renormalized
    clean_cutoff = min(weight_min * 0.5, 1e-4) if weight_min > 0 else 1e-4
    weights = ef.clean_weights(cutoff=clean_cutoff)
    exp_ret, ann_vol, sharpe = ef.portfolio_performance(risk_free_rate=rfr)

    rets = prices_opt.pct_change().dropna()
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
        "prices": prices,
        "strategy": strategy,
        "rfr": rfr,
        "lookback": lookback_years,
        "returns_model": returns_model,
        "base_currency": base_currency,
    }


def efficient_frontier(
    prices: pd.DataFrame,
    rfr: float = RISK_FREE_RATE,
    n: int = 40,
    returns_model: str = "mean_historical",
    lookback_years: int = LOOKBACK_YEARS,
) -> dict:
    """Compute EF curve, min-vol anchor, and max-Sharpe anchor."""
    mu, prices_ef = _compute_mu(prices, returns_model, rfr, lookback_years)
    S = CovarianceShrinkage(prices_ef).ledoit_wolf()

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


def monte_carlo(
    prices: pd.DataFrame,
    weights: dict,
    horizon_years: int = 3,
    n_sims: int = 1000,
) -> dict:
    """Bootstrap Monte Carlo simulation. Returns percentile paths indexed to 100."""
    rets = prices.pct_change().dropna()
    w_arr = np.array([weights.get(t, 0.0) for t in rets.columns])
    p_rets = rets.values @ w_arr

    trading_days = int(horizon_years * 252)
    rng = np.random.default_rng(42)

    paths = np.ones((n_sims, trading_days + 1)) * 100
    for i in range(n_sims):
        samples = rng.choice(p_rets, size=trading_days, replace=True)
        paths[i, 1:] = 100 * np.cumprod(1 + samples)

    return {
        "p10": np.percentile(paths, 10, axis=0),
        "p25": np.percentile(paths, 25, axis=0),
        "p50": np.percentile(paths, 50, axis=0),
        "p75": np.percentile(paths, 75, axis=0),
        "p90": np.percentile(paths, 90, axis=0),
        "horizon_years": horizon_years,
        "n_sims": n_sims,
        "trading_days": trading_days,
    }


def rebalancing_drift(
    prices: pd.DataFrame,
    target_weights: dict,
    current_weights: dict | None = None,
) -> pd.DataFrame:
    """Show how weights drifted from target and required trades.

    If current_weights is provided (from real trading history), those are used
    directly as the actual portfolio weights instead of simulating price-driven drift.
    current_weights should map ticker → portfolio weight fraction (sum ≈ 1.0).
    """
    active = {t: w for t, w in target_weights.items() if w > 0.0001 and t in prices.columns}
    if not active:
        return pd.DataFrame()

    tks = list(active.keys())
    tw = np.array([active[t] for t in tks])

    if current_weights is not None:
        # Use caller-supplied weights (from real trade history)
        cw = np.array([current_weights.get(t, 0.0) for t in tks])
        total = cw.sum()
        if total > 0:
            cw = cw / total
        else:
            cw = tw.copy()
    else:
        # Simulate drift from price movements over the past year
        window = prices[tks].tail(252).ffill().dropna()
        if window.empty or len(window) < 2:
            return pd.DataFrame()
        growth = (window.iloc[-1] / window.iloc[0]).values
        current_values = tw * growth
        cw = current_values / current_values.sum()

    drift = cw - tw

    rows = []
    for i, t in enumerate(tks):
        d = float(drift[i])
        rows.append({
            "Target %": float(tw[i]),
            "Current %": float(cw[i]),
            "Drift": d,
            "Action": "SELL" if d > 0.005 else "BUY" if d < -0.005 else "HOLD",
        })
    return pd.DataFrame(rows, index=tks)


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
