"""Quant-View Optimizer — Tab views v2.2
Rendering functions for each tab. Imported by app.py.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ── Design tokens ──────────────────────────────────────────────────────────────
BG     = "#020c18"
PANEL  = "#040f20"
BORDER = "#1e3a5f"
TEXT   = "#c8cdd4"
ACCENT = "#f5a623"
GREEN  = "#39d353"
RED    = "#ff4444"

PALETTE = [
    "#f5a623", "#39d353", "#4ea8de", "#ff6b6b",
    "#c084fc", "#fb923c", "#34d399", "#60a5fa",
    "#fbbf24", "#a78bfa",
]

_PL_BASE = dict(
    paper_bgcolor=BG, plot_bgcolor=PANEL,
    font=dict(family="Courier New", color=TEXT, size=10),
    margin=dict(t=32, b=36, l=54, r=20),
    legend=dict(bgcolor=PANEL, bordercolor=BORDER, borderwidth=1, font=dict(size=10)),
    xaxis=dict(gridcolor="#0d1f35", zerolinecolor=BORDER, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#0d1f35", zerolinecolor=BORDER, tickfont=dict(size=9)),
)


def _pl(**kw) -> dict:
    d = dict(_PL_BASE)
    d.update(kw)
    return d


def _titled(title: str, tooltip: str) -> None:
    """Render a section heading that reveals a tooltip on hover or focus."""
    st.markdown(
        f"<div class='qv-tip' tabindex='0' role='button' aria-label='{title} — hover or focus for details'"
        f" style='margin:0.8rem 0 0.4rem;'>"
        f"<span style='color:#f5a623;font-size:.82rem;font-weight:700;"
        f"letter-spacing:.06em;border-bottom:1px dashed rgba(245,166,35,0.45);'>"
        f"{title} <span style='font-size:.65rem;opacity:.7;'>ⓘ</span></span>"
        f"<div class='qv-tip-box' role='tooltip'>{tooltip}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def landing(msg: str) -> None:
    st.markdown(
        f"""<div class='qv-landing'>
        <div class='qv-feat-grid'>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>[EF]</div>
            <div class='qv-feat-title'>EFFICIENT FRONTIER</div>
            <div class='qv-feat-desc'>Visualize the full opportunity set of optimal portfolios
              from min-vol to max-return</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>[OPT]</div>
            <div class='qv-feat-title'>3 STRATEGIES</div>
            <div class='qv-feat-desc'>Max Sharpe, Min Volatility, or Max Quadratic Utility
              with configurable weight constraints</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>[BT]</div>
            <div class='qv-feat-title'>BACKTESTING</div>
            <div class='qv-feat-desc'>Historical equity curve vs SPY, QQQ, IWM
              with alpha calculation</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>[RA]</div>
            <div class='qv-feat-title'>RISK ANALYTICS</div>
            <div class='qv-feat-desc'>Correlation heatmap, marginal risk attribution,
              Sharpe, Sortino, max drawdown per asset</div>
          </div>
        </div>
        <div class='qv-landing-cta'>{msg}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 · OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════
def render_optimizer(
    r: dict,
    strategy_label: str,
    company_names: dict | None = None,
) -> None:
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}
    active  = len(weights)
    zeroed  = len(r["weights"]) - active

    rm_map = {"mean_historical": "MEAN HIST.", "capm": "CAPM", "black_litterman": "BLACK-LITTERMAN"}
    rm = rm_map.get(r.get("returns_model", "mean_historical"), "MEAN HIST.")
    ccy = r.get("base_currency", "USD")

    st.markdown(
        f"<div class='qv-status'>"
        f"<span>STRATEGY: <b class='ok'>{strategy_label.upper()}</b></span>"
        f"<span>RETURNS: <b style='color:{TEXT};'>{rm}</b></span>"
        f"<span>CURRENCY: <b style='color:{TEXT};'>{ccy}</b></span>"
        f"<span>ACTIVE: <b class='ok'>{active}</b></span>"
        f"<span>ZEROED OUT: <b class='warn'>{zeroed}</b></span>"
        f"<span>RFR: <b style='color:{TEXT};'>{r['rfr']:.1%}</b></span>"
        f"<span>LOOKBACK: <b style='color:{TEXT};'>{r['lookback']}Y</b></span>"
        f"<span class='ok'>STATUS: SOLVED ✓</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Expected Annual Return", f"{r['expected_return']:.2%}",
        help="The annualised return predicted by the selected returns model, based on historical price data over the lookback period.",
    )
    k2.metric(
        "Annual Volatility", f"{r['annual_volatility']:.2%}",
        help="The expected year-to-year fluctuation in portfolio value. Lower volatility means a smoother ride, but typically lower returns.",
    )
    k3.metric(
        "Sharpe Ratio", f"{r['sharpe_ratio']:.4f}",
        help="Return earned per unit of risk: (Expected Return − Risk-Free Rate) ÷ Volatility. Above 1.0 is generally considered strong.",
    )
    k4.metric(
        "Max Drawdown", f"{r['max_drawdown']:.2%}",
        help="The largest peak-to-trough decline recorded in the portfolio over the lookback period — a measure of worst-case historical loss.",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_t = st.columns([1.1, 0.9])

    with col_c:
        _titled(
            "OPTIMAL ALLOCATION",
            "Each slice shows the percentage of capital the optimizer assigned to that asset. "
            "Assets zeroed out were excluded because they reduced risk-adjusted return. "
            "Hover any slice for the exact weight.",
        )
        center = strategy_label.upper().replace(" ", "<br>")
        fig = go.Figure(go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.54,
            texttemplate="<b>%{label}</b><br><b>%{percent:.1%}</b>",
            textfont=dict(family="Courier New", size=12, color="#000000"),
            marker=dict(colors=PALETTE[:len(weights)], line=dict(color=BG, width=3)),
            hovertemplate="<b>%{label}</b><br>Weight: %{percent:.1%}<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{center}</b>", x=0.5, y=0.5, showarrow=False,
            font=dict(family="Courier New", size=10, color=ACCENT),
        )
        fig.update_layout(**_pl(height=370, margin=dict(t=20, b=20, l=10, r=10)),
                          showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col_t:
        _titled(
            "POSITION BREAKDOWN",
            "All active holdings ranked by weight. "
            "Wtd. Return shows each asset's proportional contribution to the portfolio's total expected return — "
            "a high-weight, low-return asset drags overall performance.",
        )
        rows = []
        for t, w in sorted(weights.items(), key=lambda x: -x[1]):
            row: dict = {"Ticker": t}
            if company_names:
                row["Company"] = company_names.get(t, "—")
            row["Weight"] = f"{w:.2%}"
            row["Wtd. Return"] = f"{r['expected_return'] * w:.2%}"
            rows.append(row)
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=300)
        st.markdown(
            f"<div style='color:#6b7a8d;font-size:.62rem;line-height:2;margin-top:8px;'>"
            f"COV MODEL &nbsp;&nbsp; LEDOIT-WOLF SHRINKAGE<br>"
            f"SOLVER &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CVXPY · CLARABEL<br>"
            f"PRICE DATA &nbsp; ADJ. CLOSE · {r['lookback']}Y LOOKBACK</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        csv_w = df.to_csv(index=False).encode("utf-8")
        st.markdown('<div class="qv-dl">', unsafe_allow_html=True)
        st.download_button(
            "↓  EXPORT WEIGHTS  CSV",
            data=csv_w,
            file_name="quant_view_weights.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 · ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
def render_analytics(r: dict, ef_fn, stats_fn, mc_fn=None) -> None:
    prices  = r["prices"]
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}
    rfr_v   = r["rfr"]

    col_ef, col_corr = st.columns(2)

    with col_ef:
        _titled(
            "EFFICIENT FRONTIER",
            "The curve plots every optimal portfolio achievable with your assets — moving right adds return but increases risk. "
            "The gold star marks Max Sharpe (best risk-adjusted return); the green diamond marks Min Volatility. "
            "The dashed Capital Market Line shows the trade-off between the risk-free rate and the risky portfolio. "
            "Your optimised portfolio is plotted in red.",
        )
        with st.spinner("Computing frontier points..."):
            ef = ef_fn(prices, rfr_v)

        ms_vol, ms_ret, ms_sr = ef["max_sharpe"]
        mv_vol, mv_ret        = ef["min_vol"]
        slope = (ms_ret - rfr_v) / ms_vol if ms_vol > 0 else 0.0

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ef["vols"], y=ef["rets"], mode="lines",
                                 name="Efficient Frontier",
                                 line=dict(color=ACCENT, width=2.5)))
        fig.add_trace(go.Scatter(
            x=[0, ms_vol * 1.45],
            y=[rfr_v, rfr_v + slope * ms_vol * 1.45],
            mode="lines", name="Capital Market Line",
            line=dict(color="#4ea8de", width=1.5, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=[mv_vol], y=[mv_ret], mode="markers+text",
            name="Min Volatility",
            marker=dict(color=GREEN, size=10, symbol="diamond"),
            text=["MIN VOL"], textposition="top right",
            textfont=dict(size=8, color=GREEN),
        ))
        fig.add_trace(go.Scatter(
            x=[ms_vol], y=[ms_ret], mode="markers+text",
            name=f"Max Sharpe ({ms_sr:.2f})",
            marker=dict(color=ACCENT, size=14, symbol="star"),
            text=["MAX SHARPE"], textposition="top right",
            textfont=dict(size=8, color=ACCENT),
        ))
        fig.add_trace(go.Scatter(
            x=[r["annual_volatility"]], y=[r["expected_return"]],
            mode="markers+text", name="Your Portfolio",
            marker=dict(color="#ff6b6b", size=12, symbol="circle",
                        line=dict(color=TEXT, width=1.5)),
            text=["PORTFOLIO"], textposition="top right",
            textfont=dict(size=8, color="#ff6b6b"),
        ))
        fig.update_layout(
            **_pl(
                height=360,
                xaxis_title="Annual Volatility",
                yaxis_title="Expected Return",
                xaxis=dict(**_PL_BASE["xaxis"], tickformat=".0%"),
                yaxis=dict(**_PL_BASE["yaxis"], tickformat=".0%"),
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_corr:
        _titled(
            "CORRELATION MATRIX",
            "Shows how closely each pair of assets moves together: +1 means lockstep, -1 means perfectly inverse, 0 means no relationship. "
            "Low or negative correlations reduce portfolio volatility through diversification. "
            "Red cells highlight pairs that tend to fall together, amplifying drawdown risk.",
        )
        corr = prices.pct_change().dropna().corr()
        fig2 = go.Figure(go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale=[[0.0, RED], [0.5, "#1a2a3a"], [1.0, ACCENT]],
            zmid=0, zmin=-1, zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate="%{text}",
            textfont=dict(size=9, color=TEXT),
            hovertemplate="<b>%{x} / %{y}</b><br>ρ = %{z:.3f}<extra></extra>",
            colorbar=dict(
                thickness=12, len=0.8, tickfont=dict(size=8, color=TEXT),
                bgcolor=PANEL, bordercolor=BORDER,
                title=dict(text="ρ", font=dict(size=10, color=TEXT)),
            ),
        ))
        fig2.update_layout(
            **_pl(
                height=360,
                margin=dict(t=32, b=36, l=60, r=20),
                xaxis=dict(tickfont=dict(size=9), color=TEXT),
                yaxis=dict(tickfont=dict(size=9), color=TEXT),
            )
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Risk Attribution
    _titled(
        "RISK ATTRIBUTION — MARGINAL CONTRIBUTION TO PORTFOLIO VOLATILITY",
        "Shows how much each asset contributes to total portfolio volatility, accounting for its weight and correlation to every other holding. "
        "A long bar means that asset is the primary driver of portfolio risk — not just because it is volatile individually, but because it moves with the rest. "
        "If one asset dominates, consider reducing its weight to distribute risk more evenly.",
    )
    rets    = prices.pct_change().dropna()
    cov_ann = rets.cov() * 252
    active  = {t: w for t, w in weights.items() if t in cov_ann.columns}
    tks     = [t for t in cov_ann.columns if t in active]
    w_arr   = np.array([active[t] for t in tks])
    p_vol   = float(np.sqrt(w_arr @ cov_ann.loc[tks, tks].values @ w_arr))
    mcv     = cov_ann.loc[tks, tks].values @ w_arr
    rc_s    = pd.Series(
        {t: float(w_arr[i] * mcv[i] / p_vol) for i, t in enumerate(tks)}
    ).sort_values(ascending=True)

    fig3 = go.Figure(go.Bar(
        x=rc_s.values, y=rc_s.index.tolist(), orientation="h",
        marker_color=PALETTE[:len(rc_s)],
        text=[f"{v:.2%}" for v in rc_s.values],
        textposition="outside", textfont=dict(size=9, color=TEXT),
        hovertemplate="<b>%{y}</b><br>Risk Contrib: %{x:.2%}<extra></extra>",
    ))
    fig3.update_layout(
        **_pl(
            height=max(220, 60 + len(rc_s) * 34),
            xaxis_title="Marginal Contribution to Volatility",
            xaxis=dict(**_PL_BASE["xaxis"], tickformat=".1%"),
        )
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Monte Carlo ────────────────────────────────────────────────────────────
    if mc_fn is not None:
        st.markdown("---")
        _titled(
            "MONTE CARLO FORWARD SIMULATION",
            "Runs thousands of simulated futures by randomly re-sampling historical daily returns and compounding them forward. "
            "The shaded bands show the spread of outcomes — the wider the band, the more uncertain the path. "
            "The solid amber line (P50) is the median expectation: half of all simulations ended above it, half below.",
        )
        mc_c1, mc_c2, _ = st.columns([1, 1, 4])
        with mc_c1:
            horizon = st.selectbox(
                "Horizon", [1, 3, 5, 10], index=1,
                format_func=lambda x: f"{x}Y", key="mc_horizon",
            )
        with mc_c2:
            n_sims = st.selectbox("Simulations", [500, 1000, 5000], index=1, key="mc_n")

        with st.spinner("Running Monte Carlo simulation..."):
            mc = mc_fn(prices, tuple(sorted(weights.items())), horizon, n_sims)

        today = datetime.today()
        x_dates = [today + timedelta(days=int(d * 365 / 252))
                   for d in range(mc["trading_days"] + 1)]

        fig_mc = go.Figure()
        fig_mc.add_trace(go.Scatter(
            x=x_dates + x_dates[::-1],
            y=list(mc["p90"]) + list(mc["p10"])[::-1],
            fill="toself", fillcolor="rgba(245,166,35,0.07)",
            line=dict(color="rgba(0,0,0,0)"),
            name="P10–P90 Range", hoverinfo="skip",
        ))
        fig_mc.add_trace(go.Scatter(
            x=x_dates + x_dates[::-1],
            y=list(mc["p75"]) + list(mc["p25"])[::-1],
            fill="toself", fillcolor="rgba(245,166,35,0.18)",
            line=dict(color="rgba(0,0,0,0)"),
            name="P25–P75 Range", hoverinfo="skip",
        ))
        fig_mc.add_trace(go.Scatter(
            x=x_dates, y=mc["p50"], mode="lines", name="Median (P50)",
            line=dict(color=ACCENT, width=2.5),
            hovertemplate="<b>Median</b><br>%{x|%b %Y}: %{y:.1f}<extra></extra>",
        ))
        fig_mc.add_trace(go.Scatter(
            x=x_dates, y=mc["p10"], mode="lines", name="P10 — Pessimistic",
            line=dict(color=RED, width=1.5, dash="dot"),
            hovertemplate="P10: %{y:.1f}<extra></extra>",
        ))
        fig_mc.add_trace(go.Scatter(
            x=x_dates, y=mc["p90"], mode="lines", name="P90 — Optimistic",
            line=dict(color=GREEN, width=1.5, dash="dot"),
            hovertemplate="P90: %{y:.1f}<extra></extra>",
        ))
        fig_mc.update_layout(
            **_pl(height=400, xaxis_title="Date",
                  yaxis_title="Portfolio Value (indexed to 100)",
                  hovermode="x unified"),
            title=dict(
                text=f"MONTE CARLO — {n_sims:,} BOOTSTRAPPED SIMULATIONS · {horizon}Y HORIZON",
                font=dict(size=10, color=ACCENT), x=0.0,
            ),
        )
        st.plotly_chart(fig_mc, use_container_width=True)

        mc1, mc2, mc3, mc4 = st.columns(4)
        final_p10 = mc["p10"][-1] / 100 - 1
        final_p50 = mc["p50"][-1] / 100 - 1
        final_p90 = mc["p90"][-1] / 100 - 1
        prob_pos = float(np.mean(
            [mc["p50"][-1]] * n_sims  # approximation using percentile bands
        ) > 100)
        mc1.metric(
            f"P10 ({horizon}Y)", f"{final_p10:.2%}",
            help=f"Pessimistic scenario: 10% of the {n_sims:,} simulated paths ended below this value at the {horizon}-year horizon.",
        )
        mc2.metric(
            f"Median ({horizon}Y)", f"{final_p50:.2%}",
            help=f"Middle outcome: half of the {n_sims:,} simulated paths ended above this value, half below.",
        )
        mc3.metric(
            f"P90 ({horizon}Y)", f"{final_p90:.2%}",
            help=f"Optimistic scenario: 90% of the {n_sims:,} simulated paths ended below this value — only 1-in-10 runs beat it.",
        )
        mc4.metric(
            "Return Range", f"{final_p10:.1%} → {final_p90:.1%}",
            help="The full spread from the pessimistic (P10) to optimistic (P90) outcome, showing the uncertainty in projected returns.",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 · BACKTEST
# ═══════════════════════════════════════════════════════════════════════════════
def render_backtest(r: dict, bt_fn) -> None:
    prices  = r["prices"]
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}

    _titled(
        "BACKTEST PERFORMANCE",
        "Shows the historical performance of your optimised portfolio, indexed to 100 at the start of the lookback period — a value of 150 means a 50% cumulative gain. "
        "The dashed benchmark line lets you see whether your portfolio outperformed the market over the same window. "
        "Note: this applies the optimizer's weights backward through history, not a live trading record.",
    )
    bm_col1, _ = st.columns([2, 5])
    with bm_col1:
        benchmark = st.selectbox("Benchmark", ["SPY", "QQQ", "IWM", "BND", "None"], index=0)
    bm_ticker = None if benchmark == "None" else benchmark

    with st.spinner("Running backtest..."):
        bt = bt_fn(prices, tuple(sorted(weights.items())), bm_ticker or "")

    colors_bt = [ACCENT, "#4ea8de", GREEN, "#c084fc"]
    fig = go.Figure()
    for i, col in enumerate(bt.columns):
        is_port = col == "Portfolio"
        fig.add_trace(go.Scatter(
            x=bt.index, y=bt[col], mode="lines", name=col,
            line=dict(color=colors_bt[i % len(colors_bt)],
                      width=2.5 if is_port else 1.8,
                      dash="solid" if is_port else "dash"),
            hovertemplate=f"<b>{col}</b><br>%{{x|%Y-%m-%d}}: %{{y:.1f}}<extra></extra>",
        ))
    fig.update_layout(
        **_pl(height=420, xaxis_title="Date", yaxis_title="Indexed to 100",
              hovermode="x unified"),
        title=dict(text="PORTFOLIO PERFORMANCE — INDEXED TO 100",
                   font=dict(size=10, color=ACCENT), x=0.0),
    )
    st.plotly_chart(fig, use_container_width=True)

    port_total = float(bt["Portfolio"].iloc[-1]) / 100 - 1
    bk1, bk2, bk3 = st.columns(3)
    bk1.metric(
        "Portfolio Total Return", f"{port_total:.2%}",
        help="Cumulative gain from the start to the end of the lookback period, using the optimised weights applied backward through history.",
    )
    if len(bt.columns) > 1:
        bm_name   = bt.columns[1]
        bm_total  = float(bt[bm_name].iloc[-1]) / 100 - 1
        alpha     = port_total - bm_total
        bk2.metric(
            f"Benchmark ({bm_name}) Return", f"{bm_total:.2%}",
            help=f"Cumulative return for {bm_name} over the identical lookback window, for direct comparison.",
        )
        bk3.metric(
            "Active Return (Alpha)", f"{alpha:.2%}",
            delta=f"{alpha:.2%}", delta_color="normal",
            help="Portfolio Total Return minus Benchmark Return. Positive alpha means the optimised weights outperformed simply buying the index.",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 · HOLDINGS
# ═══════════════════════════════════════════════════════════════════════════════
def render_holdings(r: dict, stats_fn, rb_fn=None) -> None:
    prices = r["prices"]
    rfr_v  = r["rfr"]
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}

    with st.spinner("Computing asset statistics..."):
        stats = stats_fn(prices, rfr_v)

    _titled(
        "INDIVIDUAL ASSET ANALYSIS",
        "Per-asset performance metrics calculated from raw price history over the lookback period. "
        "Ann. Return and Volatility are annualised. Sharpe measures return per unit of total risk; "
        "Sortino is similar but only penalises downside volatility — a higher Sortino than Sharpe means most volatility is on the upside. "
        "Max Drawdown is the worst peak-to-trough loss that asset suffered individually.",
    )
    ec1, ec2 = st.columns([5, 1])
    with ec2:
        st.markdown('<div class="qv-dl">', unsafe_allow_html=True)
        st.download_button(
            "↓ CSV",
            data=stats.reset_index().to_csv(index=False).encode("utf-8"),
            file_name="quant_view_holdings.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    display = stats.copy()
    display["Ann. Return"]     = display["Ann. Return"].map(lambda x: f"{x:.2%}")
    display["Ann. Volatility"] = display["Ann. Volatility"].map(lambda x: f"{x:.2%}")
    display["Max Drawdown"]    = display["Max Drawdown"].map(lambda x: f"{x:.2%}")
    display["Sharpe"]          = display["Sharpe"].map(lambda x: f"{x:.3f}")
    display["Sortino"]         = display["Sortino"].map(lambda x: f"{x:.3f}")
    with ec1:
        st.dataframe(display, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _titled(
        "SHARPE RATIO COMPARISON",
        "Ranks every asset by its individual Sharpe Ratio — excess return divided by volatility. "
        "Green bars (≥ 1.0) indicate strong risk-adjusted performance; amber (0.5–1.0) is acceptable; red (< 0.5) means the asset is poorly compensating you for the risk taken. "
        "The dashed line marks the 1.0 threshold — a common benchmark for a good standalone investment.",
    )
    sharpe_s = stats["Sharpe"].sort_values(ascending=True)
    bar_cols = [GREEN if v >= 1.0 else ACCENT if v >= 0.5 else RED for v in sharpe_s.values]

    fig4 = go.Figure(go.Bar(
        x=sharpe_s.values, y=sharpe_s.index.tolist(), orientation="h",
        marker_color=bar_cols,
        text=[f"{v:.3f}" for v in sharpe_s.values],
        textposition="outside", textfont=dict(size=9, color=TEXT),
        hovertemplate="<b>%{y}</b><br>Sharpe: %{x:.3f}<extra></extra>",
    ))
    fig4.update_layout(
        **_pl(height=max(200, 60 + len(sharpe_s) * 36), xaxis_title="Sharpe Ratio"),
        shapes=[dict(type="line", x0=1.0, x1=1.0,
                     y0=-0.5, y1=len(sharpe_s) - 0.5,
                     line=dict(color=GREEN, width=1.5, dash="dot"))],
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ── Rebalancing Drift ──────────────────────────────────────────────────────
    if rb_fn is not None:
        st.markdown("---")
        holdings_active = bool(st.session_state.get("holdings_current_weights"))
        if holdings_active:
            _titled(
                "REBALANCING DRIFT — MY HOLDINGS",
                "Current weights are derived from your actual trade history: Qty × current price → portfolio fraction. "
                "Drift shows the gap between what you actually hold today vs the optimizer's target weight. "
                "BUY means you are underweight vs target; SELL means overweight. Bars within ±0.5% are labelled HOLD.",
            )
        else:
            _titled(
                "REBALANCING DRIFT — 1-YEAR LOOKBACK",
                "Shows how your target weights have drifted due to price movements over the past year. "
                "A positive bar means that asset grew faster than the rest and is now overweight — sell to trim back to target. "
                "A negative bar means it underperformed and is now underweight — buy to top up. Bars within ±0.5% are labelled HOLD. "
                "Log trades in the Trading History section below and toggle 'Use my holdings' for real BUY/SELL guidance.",
            )

        holdings_cw = st.session_state.get("holdings_current_weights")
        cw_key = tuple(sorted(holdings_cw.items())) if holdings_cw else None
        drift_df = rb_fn(prices, tuple(sorted(weights.items())), cw_key)

        if not drift_df.empty:
            drift_colors_bar = [
                RED if drift_df.loc[t, "Action"] == "SELL"
                else GREEN if drift_df.loc[t, "Action"] == "BUY"
                else ACCENT
                for t in drift_df.index
            ]

            fig_drift = go.Figure(go.Bar(
                x=drift_df.index.tolist(),
                y=drift_df["Drift"].values,
                marker_color=drift_colors_bar,
                text=[f"{v:+.2%}" for v in drift_df["Drift"].values],
                textposition="outside", textfont=dict(size=9, color=TEXT),
                customdata=list(zip(
                    drift_df["Target %"].map(lambda x: f"{x:.2%}"),
                    drift_df["Current %"].map(lambda x: f"{x:.2%}"),
                    drift_df["Action"],
                )),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Target: %{customdata[0]}<br>"
                    "Current: %{customdata[1]}<br>"
                    "Drift: %{y:.2%}<br>"
                    "Action: %{customdata[2]}"
                    "<extra></extra>"
                ),
            ))
            fig_drift.add_hline(y=0, line_color=ACCENT, line_width=1)
            fig_drift.update_layout(
                **_pl(
                    height=280,
                    yaxis_title="Weight Drift",
                    yaxis=dict(**_PL_BASE["yaxis"], tickformat=".1%"),
                )
            )
            st.plotly_chart(fig_drift, use_container_width=True)

            # Table
            tbl = drift_df.copy()
            tbl["Target %"]  = tbl["Target %"].map(lambda x: f"{x:.2%}")
            tbl["Current %"] = tbl["Current %"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
            tbl["Drift"]     = tbl["Drift"].map(lambda x: f"{x:+.2%}" if pd.notna(x) else "N/A")
            _titled(
                "REBALANCING ACTIONS",
                "Target % is the optimizer's recommended weight. Current % is where that position sits today after a year of price movement. "
                "Drift is the gap — the amount you would need to trade to restore the optimal allocation.",
            )
            st.dataframe(tbl, use_container_width=True)

    # ── Trading History ────────────────────────────────────────────────────────
    st.markdown("---")
    _titled(
        "TRADING HISTORY",
        "Log your trades to track cost basis and unrealised P&amp;L against live prices. "
        "Add one row per trade — partial fills and multiple lots per ticker are supported. "
        "Prices refresh every 5 minutes; the P&amp;L table updates automatically as you add rows.",
    )

    default_trade_cols = {
        "Date": pd.Series(dtype="str"),
        "Ticker": pd.Series(dtype="str"),
        "Qty": pd.Series(dtype="float"),
        "Buy Price": pd.Series(dtype="float"),
    }
    existing = st.session_state.get("trade_history_data", pd.DataFrame(default_trade_cols))

    edited_trades = st.data_editor(
        existing,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn("Date Purchased", format="YYYY-MM-DD"),
            "Ticker": st.column_config.TextColumn("Ticker Symbol"),
            "Qty": st.column_config.NumberColumn("Quantity", min_value=0, format="%.4f"),
            "Buy Price": st.column_config.NumberColumn("Buy Price ($)", min_value=0, format="%.4f"),
        },
        use_container_width=True,
        key="trade_editor",
    )
    st.session_state["trade_history_data"] = edited_trades

    valid_trades = edited_trades.dropna(subset=["Ticker", "Qty", "Buy Price"])
    valid_trades = valid_trades[
        valid_trades["Ticker"].astype(str).str.strip().ne("") &
        (valid_trades["Qty"] > 0) &
        (valid_trades["Buy Price"] > 0)
    ]

    if not valid_trades.empty:
        unique_tks = [t.strip().upper() for t in valid_trades["Ticker"].unique()]

        @st.cache_data(ttl=300, show_spinner=False)
        def _fetch_current(tickers_key: tuple) -> dict:
            prices_out: dict[str, float | None] = {}
            for t in tickers_key:
                try:
                    raw = yf.download(t, period="5d", auto_adjust=True, progress=False)
                    if not raw.empty:
                        close = raw["Close"] if "Close" in raw.columns else raw.iloc[:, 0]
                        prices_out[t] = float(close.dropna().iloc[-1])
                    else:
                        prices_out[t] = None
                except Exception:
                    prices_out[t] = None
            return prices_out

        with st.spinner("Fetching current prices..."):
            cur_prices = _fetch_current(tuple(sorted(unique_tks)))

        rows = []
        for _, row in valid_trades.iterrows():
            ticker   = str(row["Ticker"]).strip().upper()
            qty      = float(row["Qty"])
            buy_px   = float(row["Buy Price"])
            cur      = cur_prices.get(ticker)
            cost     = qty * buy_px
            if cur is not None:
                cur_val  = qty * cur
                pnl      = cur_val - cost
                pnl_pct  = pnl / cost if cost > 0 else 0.0
                cur_str  = f"${cur:,.4f}"
                cv_str   = f"${cur_val:,.2f}"
                pnl_str  = f"${pnl:+,.2f}"
                pct_str  = f"{pnl_pct:+.2%}"
            else:
                cur_str = cv_str = pnl_str = pct_str = "N/A"
            rows.append({
                "Ticker":        ticker,
                "Date":          str(row.get("Date", "")),
                "Qty":           qty,
                "Buy Price":     f"${buy_px:,.4f}",
                "Current Price": cur_str,
                "Cost Basis":    f"${cost:,.2f}",
                "Current Value": cv_str,
                "P&L ($)":       pnl_str,
                "P&L (%)":       pct_str,
            })

        pnl_df = pd.DataFrame(rows)
        _titled(
            "P&amp;L SUMMARY",
            "Cost Basis is the total amount paid (Qty × Buy Price). Current Value is what that position is worth at the latest closing price. "
            "P&amp;L ($) and P&amp;L (%) show your unrealised gain or loss — positive means the position is in profit.",
        )
        st.dataframe(pnl_df, use_container_width=True, hide_index=True)

        # ── Holdings → Rebalancing feed-in ────────────────────────────────────
        use_holdings = st.toggle(
            "Use my holdings as current weights for rebalancing",
            value=False,
            help=(
                "When enabled, your trade log above is used to compute your actual current "
                "portfolio weights (Qty × current price → portfolio fraction). "
                "The rebalancing drift chart above will then show the gap between what you "
                "actually hold vs the optimizer's target — giving you real BUY/SELL guidance."
            ),
        )
        if use_holdings:
            # Build current_weights from trades × live prices
            holdings_value: dict[str, float] = {}
            for _, row in valid_trades.iterrows():
                ticker = str(row["Ticker"]).strip().upper()
                qty    = float(row["Qty"])
                cur    = cur_prices.get(ticker)
                if cur is not None and cur > 0:
                    holdings_value[ticker] = holdings_value.get(ticker, 0.0) + qty * cur
            total_val = sum(holdings_value.values())
            if total_val > 0:
                st.session_state["holdings_current_weights"] = {
                    t: v / total_val for t, v in holdings_value.items()
                }
            else:
                st.session_state["holdings_current_weights"] = None
                st.warning("No valid current prices found for your holdings — toggle disabled.")
        else:
            st.session_state["holdings_current_weights"] = None
