import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from logic import optimise, fetch_prices, RISK_FREE_RATE

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quant-View Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bloomberg-style CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global */
  html, body, [data-testid="stAppViewContainer"] {
      background-color: #0a0e17;
      color: #e0e0e0;
      font-family: 'Courier New', monospace;
  }
  [data-testid="stSidebar"] {
      background-color: #0d1220;
      border-right: 1px solid #1e2d45;
  }
  /* Headers */
  h1, h2, h3 { color: #f5a623; letter-spacing: 0.04em; }
  /* Metric cards */
  [data-testid="metric-container"] {
      background: #0d1220;
      border: 1px solid #1e3a5f;
      border-left: 3px solid #f5a623;
      border-radius: 4px;
      padding: 12px 16px;
  }
  [data-testid="stMetricValue"] { color: #f5a623; font-size: 1.6rem; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #7a8fa6; font-size: 0.75rem; text-transform: uppercase; }
  /* Buttons */
  .stButton > button {
      background: #f5a623;
      color: #0a0e17;
      font-weight: 700;
      border: none;
      border-radius: 3px;
      letter-spacing: 0.06em;
      width: 100%;
  }
  .stButton > button:hover { background: #ffc04d; color: #0a0e17; }
  /* Text input */
  .stTextArea textarea {
      background: #0d1220;
      color: #e0e0e0;
      border: 1px solid #1e3a5f;
      font-family: 'Courier New', monospace;
  }
  /* Divider */
  hr { border-color: #1e2d45; }
  /* Table */
  [data-testid="stDataFrame"] { border: 1px solid #1e3a5f; }
  /* Sidebar label */
  .sidebar-label {
      color: #7a8fa6;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 4px;
  }
  /* Status bar */
  .status-bar {
      background: #0d1220;
      border: 1px solid #1e3a5f;
      border-radius: 3px;
      padding: 6px 14px;
      font-size: 0.75rem;
      color: #7a8fa6;
      display: flex;
      gap: 24px;
  }
  .status-ok { color: #39d353; }
  .status-warn { color: #f5a623; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⬛ QUANT-VIEW")
    st.markdown("<div class='sidebar-label'>Portfolio Optimizer — MPT Engine</div>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div class='sidebar-label'>Enter Tickers (one per line)</div>", unsafe_allow_html=True)
    ticker_input = st.text_area(
        label="tickers",
        value="AAPL\nMSFT\nGOOGL\nAMZN\nNVDA",
        height=160,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(f"<div class='sidebar-label'>Risk-Free Rate</div>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#f5a623;font-size:1.1rem;font-weight:700;'>{RISK_FREE_RATE:.1%}</span>"
                "<span style='color:#7a8fa6;font-size:0.75rem;'> &nbsp;(2026 default)</span>",
                unsafe_allow_html=True)
    st.markdown("---")

    run = st.button("▶  RUN OPTIMIZATION")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-label'>Strategy</div>", unsafe_allow_html=True)
    st.markdown("<span style='color:#e0e0e0;font-size:0.85rem;'>Max Sharpe Ratio</span>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-label' style='margin-top:10px;'>Lookback</div>", unsafe_allow_html=True)
    st.markdown("<span style='color:#e0e0e0;font-size:0.85rem;'>3 Years · Adjusted Close</span>", unsafe_allow_html=True)

# ── Main header ───────────────────────────────────────────────────────────────
st.markdown("# QUANT-VIEW OPTIMIZER")
st.markdown("<div style='color:#7a8fa6;font-size:0.8rem;letter-spacing:0.08em;margin-top:-12px;margin-bottom:16px;'>MODERN PORTFOLIO THEORY · EFFICIENT FRONTIER · MAX SHARPE</div>", unsafe_allow_html=True)
st.markdown("---")

# ── Run optimization ──────────────────────────────────────────────────────────
if run:
    tickers = [t.strip().upper() for t in ticker_input.splitlines() if t.strip()]

    if len(tickers) < 2:
        st.error("Enter at least 2 tickers.")
        st.stop()

    with st.spinner("Fetching market data and computing efficient frontier..."):
        try:
            result = optimise(tickers)
        except Exception as e:
            st.error(f"Optimization failed: {e}")
            st.stop()

    weights = {k: v for k, v in result["weights"].items() if v > 0.0001}
    exp_ret = result["expected_return"]
    vol = result["annual_volatility"]
    sharpe = result["sharpe_ratio"]

    # ── Status bar ────────────────────────────────────────────────────────────
    active = len(weights)
    zeroed = len(result["weights"]) - active
    st.markdown(
        f"<div class='status-bar'>"
        f"<span>TICKERS SUBMITTED: <b style='color:#e0e0e0;'>{len(tickers)}</b></span>"
        f"<span class='status-ok'>ACTIVE POSITIONS: {active}</span>"
        f"<span class='status-warn'>ZEROED OUT: {zeroed}</span>"
        f"<span class='status-ok'>STATUS: SOLVED ✓</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI metrics ───────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Expected Annual Return", f"{exp_ret:.2%}")
    c2.metric("Annual Volatility", f"{vol:.2%}")
    c3.metric("Sharpe Ratio", f"{sharpe:.4f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chart + table row ─────────────────────────────────────────────────────
    col_chart, col_table = st.columns([1.1, 0.9])

    with col_chart:
        st.markdown("### OPTIMAL ALLOCATION")

        BLOOMBERG_PALETTE = [
            "#f5a623", "#39d353", "#4ea8de", "#ff6b6b",
            "#c084fc", "#fb923c", "#34d399", "#60a5fa",
        ]

        fig = go.Figure(go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.52,
            textinfo="label+percent",
            textfont=dict(family="Courier New", size=13, color="#e0e0e0"),
            marker=dict(
                colors=BLOOMBERG_PALETTE[:len(weights)],
                line=dict(color="#0a0e17", width=3),
            ),
            hovertemplate="<b>%{label}</b><br>Weight: %{percent}<extra></extra>",
        ))

        fig.add_annotation(
            text=f"<b>MAX<br>SHARPE</b>",
            x=0.5, y=0.5,
            font=dict(family="Courier New", size=13, color="#f5a623"),
            showarrow=False,
        )

        fig.update_layout(
            paper_bgcolor="#0a0e17",
            plot_bgcolor="#0a0e17",
            font=dict(family="Courier New", color="#e0e0e0"),
            legend=dict(
                bgcolor="#0d1220",
                bordercolor="#1e3a5f",
                borderwidth=1,
                font=dict(size=12),
            ),
            margin=dict(t=20, b=20, l=20, r=20),
            height=380,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("### POSITION BREAKDOWN")

        df = pd.DataFrame([
            {
                "Ticker": ticker,
                "Weight": f"{w:.2%}",
                "Exp. Return": f"{exp_ret * w:.2%}",
            }
            for ticker, w in sorted(weights.items(), key=lambda x: -x[1])
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=340,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:#7a8fa6;font-size:0.75rem;line-height:1.8;'>"
            f"STRATEGY &nbsp;&nbsp;&nbsp; MAX SHARPE RATIO<br>"
            f"RISK-FREE RATE &nbsp; {RISK_FREE_RATE:.1%}<br>"
            f"LOOKBACK &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 3Y · ADJ. CLOSE<br>"
            f"SOLVER &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CVXPY / CLARABEL"
            f"</div>",
            unsafe_allow_html=True,
        )

else:
    # ── Landing state ─────────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:80px 0;color:#1e3a5f;'>"
        "<div style='font-size:4rem;'>📈</div>"
        "<div style='font-size:1.1rem;letter-spacing:0.12em;margin-top:16px;color:#1e3a5f;'>"
        "ENTER TICKERS IN THE SIDEBAR AND PRESS RUN OPTIMIZATION"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
