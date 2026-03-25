"""Quant-View Optimizer — Tab views v2.1
Rendering functions for each tab. Imported by app.py.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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


def landing(msg: str) -> None:
    st.markdown(
        f"""<div class='qv-landing'>
        <div class='qv-feat-grid'>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>📐</div>
            <div class='qv-feat-title'>EFFICIENT FRONTIER</div>
            <div class='qv-feat-desc'>Visualize the full opportunity set of optimal portfolios
              from min-vol to max-return</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>⚡</div>
            <div class='qv-feat-title'>3 STRATEGIES</div>
            <div class='qv-feat-desc'>Max Sharpe, Min Volatility, or Max Quadratic Utility
              with configurable weight constraints</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>🔁</div>
            <div class='qv-feat-title'>BACKTESTING</div>
            <div class='qv-feat-desc'>Historical equity curve vs SPY, QQQ, IWM
              with alpha calculation</div>
          </div>
          <div class='qv-feat'>
            <div class='qv-feat-icon'>📊</div>
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
    k1.metric("Expected Annual Return", f"{r['expected_return']:.2%}")
    k2.metric("Annual Volatility",       f"{r['annual_volatility']:.2%}")
    k3.metric("Sharpe Ratio",            f"{r['sharpe_ratio']:.4f}")
    k4.metric("Max Drawdown",            f"{r['max_drawdown']:.2%}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_t = st.columns([1.1, 0.9])

    with col_c:
        st.markdown("### OPTIMAL ALLOCATION")
        center = strategy_label.upper().replace(" ", "<br>")
        fig = go.Figure(go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.54,
            textinfo="label+percent",
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
        st.markdown("### POSITION BREAKDOWN")
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
            "⬇  EXPORT WEIGHTS  CSV",
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
        st.markdown("### EFFICIENT FRONTIER")
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
        st.markdown("### CORRELATION MATRIX")
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
    st.markdown("### RISK ATTRIBUTION — MARGINAL CONTRIBUTION TO PORTFOLIO VOLATILITY")
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
        st.markdown("### MONTE CARLO FORWARD SIMULATION")
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
        mc1.metric(f"P10 ({horizon}Y)", f"{final_p10:.2%}", help="Pessimistic: 10% of runs ended below this")
        mc2.metric(f"Median ({horizon}Y)", f"{final_p50:.2%}", help="Middle outcome")
        mc3.metric(f"P90 ({horizon}Y)", f"{final_p90:.2%}", help="Optimistic: 90% of runs ended below this")
        mc4.metric("Return Range", f"{final_p10:.1%} → {final_p90:.1%}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 · BACKTEST
# ═══════════════════════════════════════════════════════════════════════════════
def render_backtest(r: dict, bt_fn) -> None:
    prices  = r["prices"]
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}

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
    bk1.metric("Portfolio Total Return", f"{port_total:.2%}")
    if len(bt.columns) > 1:
        bm_name   = bt.columns[1]
        bm_total  = float(bt[bm_name].iloc[-1]) / 100 - 1
        alpha     = port_total - bm_total
        bk2.metric(f"Benchmark ({bm_name}) Return", f"{bm_total:.2%}")
        bk3.metric("Active Return (Alpha)", f"{alpha:.2%}",
                   delta=f"{alpha:.2%}", delta_color="normal")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 · HOLDINGS
# ═══════════════════════════════════════════════════════════════════════════════
def render_holdings(r: dict, stats_fn, rb_fn=None) -> None:
    prices = r["prices"]
    rfr_v  = r["rfr"]
    weights = {k: v for k, v in r["weights"].items() if v > 0.0001}

    with st.spinner("Computing asset statistics..."):
        stats = stats_fn(prices, rfr_v)

    st.markdown("### INDIVIDUAL ASSET ANALYSIS")
    ec1, ec2 = st.columns([5, 1])
    with ec2:
        st.markdown('<div class="qv-dl">', unsafe_allow_html=True)
        st.download_button(
            "⬇ CSV",
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
    st.markdown("### SHARPE RATIO COMPARISON")
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
    st.markdown(
        "<div style='color:#6b7a8d;font-size:.6rem;margin-top:-8px;'>"
        "DASHED LINE AT SHARPE = 1.0 (STRONG RISK-ADJUSTED RETURN THRESHOLD)</div>",
        unsafe_allow_html=True,
    )

    # ── Rebalancing Drift ──────────────────────────────────────────────────────
    if rb_fn is not None:
        st.markdown("---")
        st.markdown("### REBALANCING DRIFT — 1-YEAR LOOKBACK")
        st.markdown(
            "<div style='color:#6b7a8d;font-size:.65rem;margin-bottom:8px;'>"
            "Shows how your target weights have drifted due to price movements over the "
            "past year. Green = underweight (BUY). Red = overweight (SELL).</div>",
            unsafe_allow_html=True,
        )

        drift_df = rb_fn(prices, tuple(sorted(weights.items())))

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
            tbl["Current %"] = tbl["Current %"].map(lambda x: f"{x:.2%}")
            tbl["Drift"]     = tbl["Drift"].map(lambda x: f"{x:+.2%}")
            st.dataframe(tbl, use_container_width=True)
