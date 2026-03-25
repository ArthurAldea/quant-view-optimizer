"""
test_logic.py — Math accuracy tests for Quant-View Optimizer.
Run with: venv/bin/python test_logic.py
"""

import math
import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np
from logic import fetch_prices, optimise, RISK_FREE_RATE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_prices(tickers: list[str], n_days: int = 756, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic daily price series (geometric random walk).
    Daily drift of 0.001 → ~25% annualised, safely above the 4% risk-free rate."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.001, 0.015, size=(n_days, len(tickers)))
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    idx = pd.bdate_range(end="2026-01-01", periods=n_days)
    return pd.DataFrame(prices, index=idx, columns=tickers)


# ── Test cases ────────────────────────────────────────────────────────────────

class TestRiskFreeRate(unittest.TestCase):
    def test_default_rate_is_4_pct(self):
        """Risk-free rate must be exactly 4.0 % per CLAUDE.md."""
        self.assertAlmostEqual(RISK_FREE_RATE, 0.04, places=6)


class TestFetchPrices(unittest.TestCase):
    def test_drops_all_nan_columns_not_rows(self):
        """Columns (tickers) with all NaN are dropped; rows are preserved."""
        prices = _make_prices(["AAPL", "MSFT", "GOOGL"])
        prices["FAKE"] = np.nan  # simulate a bad ticker

        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices}, axis=1
        )):
            result = fetch_prices(["AAPL", "MSFT", "GOOGL", "FAKE"])

        self.assertNotIn("FAKE", result.columns, "All-NaN column must be dropped")
        self.assertIn("AAPL", result.columns)
        # Row count must equal the original — no rows dropped
        self.assertEqual(len(result), len(prices))

    def test_no_rows_dropped_for_partial_nan(self):
        """Partial NaN within a valid column must not cause row removal."""
        prices = _make_prices(["AAPL", "MSFT"])
        prices.loc[prices.index[10:15], "AAPL"] = np.nan  # a few missing days

        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices}, axis=1
        )):
            result = fetch_prices(["AAPL", "MSFT"])

        self.assertEqual(len(result), len(prices), "Rows must never be dropped")


class TestOptimiseMath(unittest.TestCase):
    """Core MPT math checks using synthetic data."""

    def _run(self, tickers, prices_df):
        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices_df}, axis=1
        )):
            return optimise(tickers)

    def test_weights_sum_to_one(self):
        tickers = ["AAPL", "MSFT", "GOOGL"]
        result = self._run(tickers, _make_prices(tickers))
        total = sum(result["weights"].values())
        self.assertAlmostEqual(total, 1.0, places=4, msg="Weights must sum to 1.0")

    def test_weights_non_negative(self):
        """Default EfficientFrontier enforces long-only (no short positions)."""
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        result = self._run(tickers, _make_prices(tickers))
        for ticker, w in result["weights"].items():
            self.assertGreaterEqual(w, -1e-6, f"{ticker} weight is negative: {w}")

    def test_sharpe_ratio_formula(self):
        """Sharpe = (return - risk_free) / volatility."""
        tickers = ["AAPL", "MSFT", "GOOGL"]
        result = self._run(tickers, _make_prices(tickers))
        expected_sharpe = (result["expected_return"] - RISK_FREE_RATE) / result["annual_volatility"]
        self.assertAlmostEqual(result["sharpe_ratio"], expected_sharpe, places=3)

    def test_volatility_is_positive(self):
        tickers = ["AAPL", "MSFT", "GOOGL"]
        result = self._run(tickers, _make_prices(tickers))
        self.assertGreater(result["annual_volatility"], 0)

    def test_raises_with_single_ticker(self):
        """Optimizer must raise if fewer than 2 valid tickers remain."""
        tickers = ["AAPL"]
        with self.assertRaises((ValueError, Exception)):
            self._run(tickers, _make_prices(tickers))


class TestCryptoTicker(unittest.TestCase):
    """Ensure BTC-USD mixed with equities produces valid, accurate results."""

    TICKERS = ["AAPL", "MSFT", "BTC-USD"]

    def _make_crypto_prices(self):
        """Simulate crypto (higher vol) alongside equities."""
        rng = np.random.default_rng(7)
        n = 756
        idx = pd.bdate_range(end="2026-01-01", periods=n)

        equity_returns = rng.normal(0.0005, 0.012, size=(n, 2))
        crypto_returns = rng.normal(0.001, 0.04, size=(n, 1))  # ~4× equity vol

        all_returns = np.hstack([equity_returns, crypto_returns])
        prices = 100 * np.exp(np.cumsum(all_returns, axis=0))
        return pd.DataFrame(prices, index=idx, columns=self.TICKERS)

    def _run(self):
        prices = self._make_crypto_prices()
        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices}, axis=1
        )):
            return optimise(self.TICKERS)

    def test_crypto_weights_sum_to_one(self):
        result = self._run()
        total = sum(result["weights"].values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_crypto_weights_non_negative(self):
        result = self._run()
        for t, w in result["weights"].items():
            self.assertGreaterEqual(w, -1e-6, f"{t} weight is negative")

    def test_crypto_sharpe_formula(self):
        result = self._run()
        expected = (result["expected_return"] - RISK_FREE_RATE) / result["annual_volatility"]
        self.assertAlmostEqual(result["sharpe_ratio"], expected, places=3)

    def test_crypto_volatility_finite(self):
        """Result must not contain NaN or Inf — crypto vol can blow up the matrix."""
        result = self._run()
        self.assertTrue(math.isfinite(result["annual_volatility"]))
        self.assertTrue(math.isfinite(result["expected_return"]))
        self.assertTrue(math.isfinite(result["sharpe_ratio"]))

    def test_btc_column_retained(self):
        """BTC-USD must not be silently dropped when it has valid data."""
        prices = self._make_crypto_prices()
        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices}, axis=1
        )):
            fetched = fetch_prices(self.TICKERS)
        self.assertIn("BTC-USD", fetched.columns)

    def test_bad_crypto_ticker_dropped_not_rows(self):
        """A crypto ticker returning all NaN must be dropped without losing rows."""
        prices = self._make_crypto_prices()
        prices["ETH-USD"] = np.nan  # simulate failed fetch

        with patch("logic.yf.download", return_value=pd.concat(
            {"Close": prices}, axis=1
        )):
            result = fetch_prices(self.TICKERS + ["ETH-USD"])

        self.assertNotIn("ETH-USD", result.columns)
        self.assertEqual(len(result), len(prices))


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
