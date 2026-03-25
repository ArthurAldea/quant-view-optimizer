"""Quant-View Optimizer — F5 Guide Tab
Plain-language explanations of every concept and formula in the tool.
"""
import streamlit as st

ACCENT = "#f5a623"
TEXT   = "#c8cdd4"
GREEN  = "#39d353"
RED    = "#ff4444"


def _header(text: str) -> None:
    st.markdown(
        f"<div style='color:{ACCENT};font-size:.75rem;font-weight:700;"
        f"letter-spacing:.12em;text-transform:uppercase;margin:18px 0 6px;'>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )


def _note(text: str) -> None:
    st.markdown(
        f"<div style='background:#040f20;border-left:3px solid {ACCENT};"
        f"padding:10px 14px;border-radius:2px;color:{TEXT};font-size:.72rem;"
        f"line-height:1.8;margin:8px 0;'>{text}</div>",
        unsafe_allow_html=True,
    )


def _formula(label: str, formula: str, plain: str) -> None:
    st.markdown(
        f"<div style='background:#040f20;border:1px solid #1e3a5f;border-radius:2px;"
        f"padding:12px 16px;margin:8px 0;'>"
        f"<div style='color:{ACCENT};font-size:.65rem;font-weight:700;"
        f"letter-spacing:.1em;margin-bottom:6px;'>{label}</div>"
        f"<div style='color:#4ea8de;font-family:\"Courier New\",monospace;"
        f"font-size:.8rem;margin-bottom:8px;'>{formula}</div>"
        f"<div style='color:{TEXT};font-size:.7rem;line-height:1.7;'>{plain}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_guide() -> None:
    st.markdown(
        f"<div style='color:{ACCENT};font-size:1rem;font-weight:700;"
        f"letter-spacing:.1em;margin-bottom:4px;'>◈ STOCKSBRO — COMPLETE GUIDE</div>"
        f"<div style='color:#6b7a8d;font-size:.65rem;letter-spacing:.08em;"
        f"margin-bottom:18px;'>Everything explained from first principles — no finance background required</div>",
        unsafe_allow_html=True,
    )

    # ── SECTION 1: What is this tool? ─────────────────────────────────────────
    with st.expander("WHAT IS THIS TOOL?", expanded=True):
        st.markdown(
            """
**StocksBro is a portfolio calculator.** You give it a list of stocks or funds,
and it figures out the *best possible way to split your money* across those assets — based on
their historical prices and a branch of finance called Modern Portfolio Theory (MPT).

Think of it like this: if you're making a fruit smoothie, you don't just throw in equal
amounts of everything. Some ingredients complement each other; others clash. This tool
does the same for investments — it finds the blend where you get the most return for
the least risk, or whichever goal you choose.

**What you need to use it:**
1. A list of stock or fund ticker symbols (e.g., AAPL = Apple, SPY = S&P 500 index fund)
2. Choose a strategy (explained below)
3. Press **RUN OPTIMIZATION**

That's it. The tool fetches real price data, runs the math, and shows you the optimal allocation.
            """
        )

    # ── SECTION 2: Key concepts ────────────────────────────────────────────────
    with st.expander("KEY CONCEPTS — STOCKS, TICKERS, PORTFOLIOS"):
        _header("What is a stock?")
        st.markdown(
            """
A **stock** (also called a share or equity) is a tiny slice of ownership in a company.
When you buy one share of Apple (AAPL), you own a microscopic piece of Apple Inc.
If Apple becomes more valuable, your share is worth more. If it does poorly, it's worth less.

**Tickers** are the short codes used to identify each stock on an exchange. Examples:
- `AAPL` = Apple
- `MSFT` = Microsoft
- `GOOGL` = Alphabet (Google's parent company)
- `SPY` = An ETF that tracks the S&P 500 (top 500 US companies at once)
- `BTC-USD` = Bitcoin priced in US dollars
            """
        )
        _header("What is an ETF?")
        st.markdown(
            """
An **ETF (Exchange-Traded Fund)** is a basket of many stocks bundled together.
When you buy SPY, you're effectively buying tiny pieces of all 500 companies in the S&P 500 index.
ETFs let you diversify instantly without picking individual companies.
            """
        )
        _header("What is a portfolio?")
        st.markdown(
            """
A **portfolio** is your total collection of investments. Instead of putting all your money in
one stock, you spread it across several — this is called **diversification**. The core idea:
if one investment tanks, the others can cushion the blow.

This tool asks: *given these assets, what's the smartest way to split my money?*
            """
        )

    # ── SECTION 3: Risk and Return ─────────────────────────────────────────────
    with st.expander("RISK VS. RETURN — THE FUNDAMENTAL TRADE-OFF"):
        _note(
            "The single most important idea in all of investing: <b>higher potential returns "
            "always come with higher risk.</b> There is no free lunch. The question is always "
            "whether the extra risk is worth the extra expected return."
        )
        _header("Return")
        st.markdown(
            """
**Return** is how much your investment grew (or shrank) over a period.
If you invested $100 and it's now worth $112, your return is +12%.

This tool shows **Annual Return** — what you'd expect to gain per year, on average,
based on the last 1–10 years of historical data. This is an *estimate*, not a guarantee.
            """
        )
        _header("Volatility (Risk)")
        st.markdown(
            """
**Volatility** measures how wildly a stock's price bounces around day to day.

- A **low-volatility** stock (e.g., a utility company) moves slowly and predictably.
- A **high-volatility** stock (e.g., a startup or crypto) can swing 10% in a single day.

High volatility means uncertainty — the outcome could be much better *or* much worse than expected.
Mathematically, volatility is the **standard deviation** of daily returns, scaled to one year.
            """
        )
        _formula(
            "ANNUAL VOLATILITY",
            "σ = std(daily_returns) × √252",
            "We take the standard deviation of daily price changes and multiply by √252 "
            "(there are ~252 trading days in a year) to convert it to an annual figure. "
            "A 20% annual volatility means returns in any given year are typically within "
            "±20% of the expected value — but can be further in rare years."
        )

    # ── SECTION 4: MPT and the Efficient Frontier ─────────────────────────────
    with st.expander("MODERN PORTFOLIO THEORY & THE EFFICIENT FRONTIER"):
        st.markdown(
            """
**Modern Portfolio Theory (MPT)** was invented by Harry Markowitz in 1952. He won the Nobel
Prize for it. The core insight: **combining assets that don't move in lockstep reduces your
overall risk without necessarily reducing your return.**

Imagine two ice cream shops: one sells hot drinks, one sells cold. They do terribly in opposite
weather. But if you own both, your *combined* business stays steady year-round. That's
diversification in action.

MPT turns this intuition into math. It looks at:
1. Each asset's expected return
2. Each asset's volatility
3. How each pair of assets moves together (correlation)

Then it finds the portfolio that, for any given level of risk, gives you the highest possible return.
            """
        )
        _header("The Efficient Frontier")
        st.markdown(
            """
The **Efficient Frontier** is a curve showing every *optimal* portfolio possible from your assets.
Every point on the curve is a different allocation that you can't improve without accepting more risk.

- **Left end of the curve** = minimum volatility portfolio (safest combination)
- **Upper right** = higher return, but also higher risk

Any portfolio *below* the curve is inefficient — you're accepting the same risk for less return.
You can see this chart in the **F2 ANALYTICS** tab.
            """
        )
        _header("Capital Market Line (CML)")
        st.markdown(
            """
The **Capital Market Line** is the straight line drawn from the risk-free rate (e.g., 4% from
government bonds) tangentially to the Efficient Frontier. The point where it touches the curve
is the **maximum Sharpe portfolio** — the single best risk-adjusted return available from your assets.
            """
        )
        _header("Correlation")
        _formula(
            "CORRELATION COEFFICIENT",
            "ρ (rho) = cov(A,B) / (σ_A × σ_B)   |   range: −1 to +1",
            "ρ = +1 means the two assets move perfectly together (no diversification benefit). "
            "ρ = −1 means they move perfectly opposite (maximum hedging). "
            "ρ = 0 means they move independently. "
            "The correlation heatmap in F2 shows all pair-wise correlations. "
            "You want low correlations — that's what makes diversification work."
        )

    # ── SECTION 5: Strategies ─────────────────────────────────────────────────
    with st.expander("OPTIMIZATION STRATEGIES"):
        _header("Max Sharpe Ratio")
        _formula(
            "SHARPE RATIO",
            "Sharpe = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility",
            "The Sharpe Ratio measures how much return you get per unit of risk. "
            "A ratio of 1.0 means you earned 1% of extra return for every 1% of risk taken — decent. "
            "Above 2.0 is excellent. Below 0.5 is poor. "
            "Max Sharpe finds the allocation that maximizes this number — the best bang for your risk buck."
        )
        _note(
            "The <b>Risk-Free Rate</b> (default 4%) is what you'd earn by doing nothing risky — "
            "like parking your money in government bonds. It's the baseline: any investment should "
            "ideally beat it, or why take the risk?"
        )

        _header("Min Volatility")
        st.markdown(
            """
This strategy ignores returns entirely and just finds the portfolio with the **lowest possible
price swings**. Useful if you want a calm, steady ride and don't need to maximize growth.
Often results in more diversified allocations than Max Sharpe.
            """
        )

        _header("Max Quadratic Utility")
        st.markdown(
            """
This strategy balances return and risk using a formula that penalizes variance:

**Utility = Expected Return − (½ × risk_aversion × Variance)**

It's a middle ground between Max Sharpe and Min Volatility — directly trading off
return against risk with an explicit penalty for volatility.
            """
        )

    # ── SECTION 6: Returns Models ─────────────────────────────────────────────
    with st.expander("RETURNS MODELS — HOW FUTURE RETURNS ARE ESTIMATED"):
        _header("Mean Historical Return")
        st.markdown(
            """
The simplest approach: take the average of daily returns over the lookback period and
annualize it. Assumes the past is a reasonable guide to the future. Works well for
stable, mature assets. Can mislead for assets that had unusual recent performance.
            """
        )
        _formula(
            "MEAN HISTORICAL RETURN",
            "μ = ((1 + mean_daily_return)^252) − 1",
            "We compound the average daily return up to an annual figure."
        )

        _header("CAPM (Capital Asset Pricing Model)")
        _formula(
            "CAPM",
            "μ_i = R_f + β_i × (R_market − R_f)",
            "CAPM estimates each asset's expected return based on how much it moves with "
            "the overall market (β = beta). β > 1 means the asset amplifies market moves; "
            "β < 1 means it's more stable. R_f is the risk-free rate. R_market is the "
            "expected market return (estimated from SPY). "
            "This model connects each stock's expected return to the whole economy."
        )

        _header("Black-Litterman Model")
        st.markdown(
            """
The **Black-Litterman model** (1990, Goldman Sachs) is a more sophisticated approach.
Instead of just using historical averages, it starts from **market-implied returns** —
what the market collectively *believes* each stock should return, based on current
market capitalizations. It uses company sizes as a prior belief, then uses Bayesian
statistics to produce more stable, diversified estimates.

**Why is it better?** Mean historical returns can produce extreme, concentrated allocations
because a stock that happened to do well recently looks very attractive. BL produces
smoother estimates grounded in what the entire market is pricing in.

The tool fetches market caps from Yahoo Finance to compute the prior.
            """
        )

    # ── SECTION 7: Risk Metrics ────────────────────────────────────────────────
    with st.expander("RISK METRICS — SHARPE, SORTINO, MAX DRAWDOWN"):
        _formula(
            "SHARPE RATIO",
            "Sharpe = (Ann. Return − Risk-Free Rate) / Ann. Volatility",
            "Return per unit of total risk. Uses all volatility (both up and down days)."
        )
        _formula(
            "SORTINO RATIO",
            "Sortino = (Ann. Return − Risk-Free Rate) / Downside Deviation",
            "Like Sharpe, but only penalizes downward volatility. Going up fast doesn't count "
            "as risk — only going down does. A higher Sortino than Sharpe means the asset's "
            "volatility is mostly on the upside, which is good."
        )
        _formula(
            "MAX DRAWDOWN",
            "Max DD = min((Portfolio Value − Peak Value) / Peak Value)",
            "The largest peak-to-trough decline in portfolio value. If your portfolio hit "
            "$100K, then fell to $65K before recovering, the max drawdown is −35%. "
            "This measures the worst-case loss you would have experienced if you held. "
            "Lower (less negative) is better."
        )

    # ── SECTION 8: Covariance ──────────────────────────────────────────────────
    with st.expander("COVARIANCE & LEDOIT-WOLF SHRINKAGE"):
        st.markdown(
            """
The **covariance matrix** captures how every pair of assets in your portfolio moves together.
It's the engine of MPT — without it, we can't compute portfolio volatility or solve the
optimization problem.

**The problem:** with many assets and limited data, the raw (sample) covariance matrix
tends to be noisy and unreliable. Small historical quirks get amplified, producing
extreme allocations.

**Ledoit-Wolf shrinkage** is a mathematical technique that "shrinks" the noisy empirical
covariance matrix toward a more stable target (the identity matrix). The result is a cleaner,
more reliable estimate of true co-movement — leading to better, more robust portfolios.

Think of it like applying noise reduction to an audio recording before analyzing it.
This is why the tool uses Ledoit-Wolf instead of the raw sample covariance.
            """
        )

    # ── SECTION 9: Monte Carlo ────────────────────────────────────────────────
    with st.expander("MONTE CARLO SIMULATION"):
        st.markdown(
            """
**Monte Carlo simulation** is a way of exploring the future by running thousands of
possible scenarios. Here's how it works for a portfolio:

1. We take all the daily returns your portfolio *actually experienced* historically.
2. We randomly resample those returns thousands of times to simulate possible futures.
3. Each simulation traces a different path your portfolio *could* take over the horizon.
4. We summarize the range of outcomes using **percentiles**.

The **fan chart** in F2 ANALYTICS shows:
- **P90 line (green):** 90% of simulations ended below this — an optimistic outcome
- **P50 line (orange):** the median — half of all runs were better, half were worse
- **P10 line (red):** 10% of simulations ended below this — a pessimistic outcome
- **Shaded bands:** the cone of uncertainty widens as you look further into the future

**Important caveat:** this assumes future daily returns are drawn from the same
distribution as the past. Real markets can behave differently — this is a
probabilistic *estimate*, not a crystal ball.
            """
        )

    # ── SECTION 10: Rebalancing ───────────────────────────────────────────────
    with st.expander("REBALANCING DRIFT"):
        st.markdown(
            """
When you set up a portfolio, you target certain weights — e.g., 40% Apple, 30% Microsoft,
30% Google. Over time, as prices move differently, those weights **drift**. If Apple doubles
and the others stay flat, Apple now represents ~57% of your portfolio, not 40%.

**Why does this matter?**
- Your portfolio is no longer optimized the way you intended
- You may have unintentionally become overexposed to your best performer
- Rebalancing (selling what grew, buying what lagged) restores the original risk profile

The **Rebalancing Drift** section in F4 HOLDINGS shows:
- **Target %:** the weight from the optimization
- **Current %:** what the weight would be today (based on 1 year of price drift)
- **Drift:** how far it has moved (+ve = overweight, −ve = underweight)
- **Action:** SELL if overweight by >0.5%, BUY if underweight, HOLD otherwise
            """
        )

    # ── SECTION 11: Multi-Currency ────────────────────────────────────────────
    with st.expander("MULTI-CURRENCY SUPPORT"):
        st.markdown(
            """
All prices fetched from Yahoo Finance are in their native currency (usually USD).
If you're based in Europe or another region, you may want to see returns in your
home currency.

When you select a **Base Currency** other than USD in the sidebar, the tool:
1. Fetches the daily USD → [currency] exchange rate (e.g., USDEUR=X)
2. Multiplies all asset prices by that rate
3. Runs the entire optimization in your chosen currency

This removes the **FX distortion** from global portfolios — a 10% stock gain means
less if USD weakened 5% against EUR during the same period.

**Tickers with known FX issues:** Stocks already priced in your target currency
(e.g., European stocks traded on EU exchanges) may double-convert. Use with awareness.
            """
        )

    # ── SECTION 12: Saved Portfolios ─────────────────────────────────────────
    with st.expander("SAVED PORTFOLIOS"):
        st.markdown(
            """
The **Saved Portfolios** section in the sidebar lets you store multiple watchlists
during a session. Type a name and press **SAVE** to snapshot your current ticker list.
Press **LOAD** to restore any saved set of tickers.

Use this to:
- Compare different portfolios side by side (run one, note metrics, load another, compare)
- Save a "current portfolio" vs an "alternative" you're considering
- Quickly switch between different client or scenario watchlists
            """
        )

    # ── SECTION 13: How to use each tab ──────────────────────────────────────
    with st.expander("HOW TO USE EACH TAB"):
        _header("F1 · OPTIMIZER")
        st.markdown(
            """
The main results tab. After pressing RUN OPTIMIZATION, you'll see:
- **4 KPI cards:** Return, Volatility, Sharpe, Max Drawdown at a glance
- **Donut chart:** visual split of your allocation across assets
- **Position table:** exact weights, company names, and contribution to expected return
- **Export CSV:** download the weights for use in a spreadsheet or brokerage
            """
        )
        _header("F2 · ANALYTICS")
        st.markdown(
            """
Deep-dive on risk and the mathematical foundation:
- **Efficient Frontier:** see where your portfolio sits on the risk/return spectrum
- **Correlation Matrix:** spot which assets move together (warmer colors = more correlated)
- **Risk Attribution:** which assets contribute most to total portfolio volatility
- **Monte Carlo:** visualize the range of possible future outcomes
            """
        )
        _header("F3 · BACKTEST")
        st.markdown(
            """
See how your optimized portfolio *would have performed* if you'd held it over the
historical lookback period, compared to a benchmark (SPY, QQQ, IWM, or BND).
The **Alpha** metric shows how much you outperformed (or underperformed) the benchmark.
Note: this is in-sample — the portfolio was optimized on the same data, so it looks
better than it would in true out-of-sample testing.
            """
        )
        _header("F4 · HOLDINGS")
        st.markdown(
            """
Individual asset analysis:
- **Stats table:** per-ticker return, volatility, Sharpe, Sortino, max drawdown
- **Sharpe chart:** quickly see which assets are pulling their weight
- **Rebalancing drift:** how much each position has drifted from target over the past year
            """
        )
        _header("F5 · GUIDE")
        st.markdown("You're reading it.")

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#2a4060;font-size:.6rem;text-align:center;"
        "margin-top:32px;letter-spacing:.1em;'>"
        "STOCKSBRO · BUILT WITH PYPFOPT · DATA FROM YAHOO FINANCE · "
        "FOR EDUCATIONAL AND INFORMATIONAL USE ONLY · NOT FINANCIAL ADVICE</div>",
        unsafe_allow_html=True,
    )
