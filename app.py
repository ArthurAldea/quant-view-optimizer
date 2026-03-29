"""StocksBro — Main Entry Point v2.2
Bloomberg Terminal-style professional portfolio analytics.
"""
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from logic import (
    CURRENCIES,
    LOOKBACK_YEARS,
    RETURN_MODELS,
    RISK_FREE_RATE,
    STRATEGIES,
    asset_stats,
    backtest,
    efficient_frontier,
    get_company_names,
    monte_carlo,
    optimise,
    rebalancing_drift,
    search_tickers,
)
from views import landing, render_analytics, render_backtest, render_holdings, render_optimizer
from guide import render_guide

PRESETS: dict[str, str] = {
    "MAG 7":      "AAPL\nMSFT\nNVDA\nGOOGL\nAMZN\nMETA\nTSLA",
    "S&P TOP 10": "AAPL\nMSFT\nNVDA\nAMZN\nGOOGL\nMETA\nBRK-B\nLLY\nJPM\nV",
    "FAANG+":     "META\nAAPL\nAMZN\nNFLX\nGOOGL\nMSFT",
    "DIVIDEND":   "JNJ\nKO\nPG\nXOM\nABBV\nWMT\nT\nVZ\nMRK\nCL",
    "GLOBAL ETF": "SPY\nQQQ\nEFA\nEEM\nIWM\nGLD\nTLT\nBND",
    "CRYPTO+":    "BTC-USD\nETH-USD\nSOL-USD\nLINK-USD\nADA-USD",
}

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StocksBro | Portfolio Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bloomberg Terminal CSS ─────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.block-container{
  background:#020c18!important;color:#c8cdd4;font-family:'JetBrains Mono','Courier New',monospace;}
[data-testid="stSidebar"]{background:#040f20!important;border-right:1px solid #1e2d45;}
[data-testid="stSidebar"] *{font-family:'JetBrains Mono','Courier New',monospace!important;}
.block-container{padding-top:0.5rem!important;max-width:100%!important;}
/* Hide Streamlit top toolbar so the header banner is never cut off */
header[data-testid="stHeader"]{display:none!important;}
#MainMenu{display:none!important;}
[data-testid="stToolbar"]{display:none!important;}
[data-testid="stDecoration"]{display:none!important;}
/* Hide sidebar collapse/expand button (shows keyboard_double_ icon) */
[data-testid="stSidebarCollapseButton"]{display:none!important;}
button[kind="headerNoPadding"]{display:none!important;}
h1,h2,h3{color:#f5a623;letter-spacing:.06em;}
h1{font-size:1.2rem!important;}h2{font-size:.95rem!important;}h3{font-size:.82rem!important;}
[data-testid="metric-container"]{background:#071628;border:1px solid #1e3a5f;
  border-left:3px solid #f5a623;border-radius:2px;padding:10px 14px;}
[data-testid="stMetricValue"]{color:#f5a623;font-size:1.4rem!important;font-weight:700;}
[data-testid="stMetricLabel"]{color:#9aabb8;font-size:.75rem!important;
  text-transform:uppercase;letter-spacing:.1em;}
[data-testid="stMetricDeltaIcon"],[data-testid="stMetricDelta"]{font-size:.75rem!important;}
.stButton>button{background:#f5a623;color:#020c18;font-weight:700;
  font-family:'JetBrains Mono','Courier New',monospace;border:none;border-radius:2px;
  letter-spacing:.08em;font-size:.875rem;width:100%;padding:10px;
  transition:background .15s ease,color .15s ease;}
.stButton>button:hover{background:#ffc04d;color:#020c18;}
.stTextArea textarea{background:#040f20!important;color:#c8cdd4!important;
  border:1px solid #1e3a5f!important;font-family:'JetBrains Mono','Courier New',monospace!important;
  font-size:.875rem!important;}
div[data-baseweb="select"]>div{background:#040f20!important;color:#c8cdd4!important;
  border-color:#1e3a5f!important;}
[data-testid="stSlider"] > div > div > div{background:#1e3a5f;}
[data-testid="stTabs"]{border-bottom:2px solid #f5a623;margin-bottom:12px;}
button[data-baseweb="tab"]{background:#040f20!important;color:#9aabb8!important;
  font-family:'JetBrains Mono','Courier New',monospace!important;font-size:.8rem!important;
  font-weight:700!important;letter-spacing:.12em!important;text-transform:uppercase!important;
  border:1px solid #1e2d45!important;border-bottom:none!important;
  border-radius:2px 2px 0 0!important;padding:6px 20px!important;margin-right:3px!important;
  transition:background .15s ease,color .15s ease,border-color .15s ease!important;}
button[data-baseweb="tab"]:hover{color:#c8cdd4!important;background:#0d1f35!important;}
button[data-baseweb="tab"][aria-selected="true"]{background:#f5a623!important;
  color:#020c18!important;border-color:#f5a623!important;}
[data-testid="stDataFrame"]{border:1px solid #1e3a5f!important;border-radius:2px;}
hr{border-color:#1e2d45;margin:5px 0;}
.qv-label{color:#9aabb8;font-size:.75rem;text-transform:uppercase;
  letter-spacing:.12em;margin-bottom:3px;margin-top:10px;}
.qv-status{background:#040f20;border:1px solid #1e3a5f;border-radius:2px;
  padding:6px 14px;font-size:.8rem;color:#9aabb8;display:flex;
  flex-wrap:wrap;gap:20px;margin-bottom:12px;}
.ok{color:#39d353;font-weight:700;}.warn{color:#f5a623;font-weight:700;}
.neg{color:#ff4444;font-weight:700;}
.qv-landing{padding:30px 10px;}
.qv-feat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;
  max-width:960px;margin:0 auto;}
@media(max-width:720px){.qv-feat-grid{grid-template-columns:repeat(2,1fr);}}
.qv-feat{background:#040f20;border:1px solid #1e3a5f;border-left:3px solid rgba(245,166,35,0.3);
  border-radius:2px;padding:16px 14px;text-align:center;
  transition:background .15s ease,border-color .15s ease;}
.qv-feat:hover{background:#071628;border-left-color:#f5a623;}
.qv-feat-icon{font-size:1.1rem;font-weight:700;color:#f5a623;
  letter-spacing:.06em;margin-bottom:8px;}
.qv-feat-title{color:#f5a623;font-size:.8rem;font-weight:700;
  letter-spacing:.1em;margin-bottom:5px;}
.qv-feat-desc{color:#9aabb8;font-size:.8rem;line-height:1.7;}
.qv-landing-cta{text-align:center;margin-top:24px;color:#f5a623;
  font-size:.875rem;letter-spacing:.12em;}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]{
  flex:1 1 0%!important;min-width:0!important;}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton{
  width:100%!important;}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button{
  background:#040f20!important;color:#c8cdd4!important;
  border:1px solid #1e3a5f!important;font-size:.75rem!important;
  padding:0!important;letter-spacing:.02em!important;
  height:32px!important;min-height:32px!important;max-height:32px!important;
  width:100%!important;white-space:nowrap!important;overflow:hidden!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  text-align:center!important;box-sizing:border-box!important;
  transition:background .15s ease,border-color .15s ease,color .15s ease!important;}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button:hover{
  background:#0d1f35!important;border-color:#f5a623!important;color:#f5a623!important;}
.qv-dl>div>button,.qv-dl>div>a{background:transparent!important;
  color:#f5a623!important;border:1px solid #1e3a5f!important;
  font-size:.75rem!important;padding:6px 14px!important;width:auto!important;
  transition:border-color .15s ease!important;}
.qv-dl>div>button:hover{border-color:#f5a623!important;}
[data-testid="stStatusWidget"]{background:#040f20;border:1px solid #1e3a5f;
  border-radius:2px;font-size:.8rem;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:#020c18;}
::-webkit-scrollbar-thumb{background:#1e3a5f;border-radius:3px;}
details summary{color:#f5a623!important;font-size:.8rem!important;
  font-weight:700!important;letter-spacing:.1em!important;cursor:pointer;}
details{background:#040f20!important;border:1px solid #1e3a5f!important;
  border-radius:2px!important;padding:10px 14px!important;margin:6px 0!important;}
/* Hover/focus tooltips on section headings */
.qv-tip{position:relative;display:inline-block;cursor:help;}
.qv-tip:focus{outline:1px dashed rgba(245,166,35,0.5);outline-offset:2px;}
.qv-tip-box{visibility:hidden;opacity:0;pointer-events:none;
  background:#040f20;border:1px solid #f5a623;color:#c8cdd4;
  font-family:'JetBrains Mono','Courier New',monospace;font-size:.8rem;line-height:1.7;
  font-weight:400;letter-spacing:0;text-transform:none;
  padding:8px 12px;border-radius:2px;
  position:absolute;z-index:9999;width:340px;
  bottom:130%;left:0;
  transition:opacity .15s ease;}
.qv-tip:hover .qv-tip-box,.qv-tip:focus .qv-tip-box{visibility:visible;opacity:1;}
/* cursor affordance on all clickable custom elements */
.qv-tip,.qv-feat{cursor:pointer;}
</style>""", unsafe_allow_html=True)

ACCENT = "#f5a623"
TEXT   = "#c8cdd4"

# ── Session state ──────────────────────────────────────────────────────────────
if "ticker_input"      not in st.session_state:
    st.session_state["ticker_input"] = "AAPL\nMSFT\nGOOGL\nAMZN\nNVDA"
if "result"            not in st.session_state:
    st.session_state.result = None
if "company_names"     not in st.session_state:
    st.session_state.company_names = None
if "saved_portfolios"  not in st.session_state:
    st.session_state.saved_portfolios: dict = {}
if "lookup_results"    not in st.session_state:
    st.session_state.lookup_results: list = []
if "result_params"     not in st.session_state:
    st.session_state["result_params"] = None
if "trade_history"     not in st.session_state:
    st.session_state["trade_history"] = []
if "mc_n"              not in st.session_state:
    st.session_state["mc_n"] = 1000
if "mc_horizon"        not in st.session_state:
    st.session_state["mc_horizon"] = 3
if "_pending_ticker"   not in st.session_state:
    st.session_state["_pending_ticker"] = None


# ── Cached computation wrappers ───────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _run_opt(
    tickers: tuple,
    strategy: str,
    rfr: float,
    lookback: int,
    w_min: float,
    w_max: float,
    returns_model: str,
    base_currency: str,
) -> dict:
    return optimise(list(tickers), strategy, rfr, lookback, w_min, w_max, returns_model, base_currency)


@st.cache_data(ttl=3600, show_spinner=False)
def _run_ef(prices: pd.DataFrame, rfr: float) -> dict:
    return efficient_frontier(prices, rfr)


@st.cache_data(ttl=3600, show_spinner=False)
def _run_bt(prices: pd.DataFrame, weights_key: tuple, benchmark: str) -> pd.DataFrame:
    return backtest(prices, dict(weights_key), benchmark or None)


@st.cache_data(ttl=3600, show_spinner=False)
def _run_stats(prices: pd.DataFrame, rfr: float) -> pd.DataFrame:
    return asset_stats(prices, rfr)


@st.cache_data(ttl=3600, show_spinner=False)
def _run_mc(prices: pd.DataFrame, weights_key: tuple, horizon: int, n_sims: int) -> dict:
    return monte_carlo(prices, dict(weights_key), horizon, n_sims)


def _run_rb(
    prices: pd.DataFrame,
    weights_key: tuple,
    current_weights_key: tuple | None = None,
) -> pd.DataFrame:
    cw = dict(current_weights_key) if current_weights_key else None
    return rebalancing_drift(prices, dict(weights_key), cw)


@st.cache_data(ttl=86400, show_spinner=False)
def _get_names(tickers_key: tuple) -> dict[str, str]:
    return get_company_names(list(tickers_key))


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='color:#f5a623;font-size:1.15rem;font-weight:700;"
        "letter-spacing:.12em;padding:4px 0 2px;'>◈ STOCKSBRO</div>"
        "<div style='color:#9aabb8;font-size:.75rem;letter-spacing:.1em;"
        "text-transform:uppercase;margin-bottom:10px;'>Professional Portfolio Analytics</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Preset watchlist buttons
    st.markdown("<div class='qv-label'>Quick Load Watchlist</div>", unsafe_allow_html=True)
    preset_cols = st.columns(2)
    for i, (pname, ptickers) in enumerate(PRESETS.items()):
        with preset_cols[i % 2]:
            if st.button(pname, key=f"p_{pname}", use_container_width=True):
                st.session_state["ticker_input"] = ptickers

    # Apply any pending ticker add BEFORE text_area is instantiated
    if st.session_state["_pending_ticker"]:
        current = st.session_state["ticker_input"].strip()
        tickers_existing = [t.strip().upper() for t in current.splitlines() if t.strip()]
        sym = st.session_state["_pending_ticker"]
        if sym.upper() not in tickers_existing:
            st.session_state["ticker_input"] = current + ("\n" if current else "") + sym
        st.session_state["_pending_ticker"] = None

    st.markdown(
        "<div class='qv-label' style='margin-top:8px;'>Tickers — one per line</div>"
        "<div style='color:#9aabb8;font-size:.75rem;line-height:1.7;margin-bottom:4px;'>"
        "US: AAPL &nbsp;·&nbsp; ASX: CBA.AX &nbsp;·&nbsp; Crypto: BTC-USD</div>",
        unsafe_allow_html=True,
    )
    ticker_input = st.text_area(
        "tickers", key="ticker_input",
        height=130, label_visibility="collapsed",
    )

    # ── Ticker Lookup ──────────────────────────────────────────────────────────
    st.markdown("<div class='qv-label' style='margin-top:6px;'>Ticker Lookup</div>",
                unsafe_allow_html=True)
    lk1, lk2 = st.columns([5, 1])
    with lk1:
        lookup_query = st.text_input(
            "lookup", placeholder="Apple",
            label_visibility="collapsed", key="lookup_input",
        )
    with lk2:
        if st.button("FIND", key="btn_lookup", use_container_width=True):
            if lookup_query.strip():
                st.session_state.lookup_results = search_tickers(lookup_query.strip())
            else:
                st.session_state.lookup_results = []

    if st.session_state.lookup_results:
        for res in st.session_state.lookup_results:
            rc1, rc2 = st.columns([5, 1])
            with rc1:
                st.markdown(
                    f"<div style='font-size:.75rem;color:{TEXT};padding-top:6px;line-height:1.5;'>"
                    f"<b style='color:{ACCENT};'>{res['symbol']}</b>"
                    f"&nbsp;·&nbsp;{res['name']}"
                    f"<span style='color:#9aabb8;'>&nbsp;({res['exchange']})</span></div>",
                    unsafe_allow_html=True,
                )
            with rc2:
                if st.button("+", key=f"add_{res['symbol']}", use_container_width=True):
                    st.session_state["_pending_ticker"] = res["symbol"]
                    st.session_state.lookup_results = []
                    st.rerun()
    elif lookup_query and not st.session_state.lookup_results:
        pass  # no results shown until FIND is pressed

    st.markdown("<div class='qv-label'>Strategy</div>", unsafe_allow_html=True)
    strategy_label = st.selectbox(
        "Strategy", list(STRATEGIES.keys()), index=0, label_visibility="collapsed",
    )
    strategy = STRATEGIES[strategy_label]

    st.markdown("<div class='qv-label'>Returns Model</div>", unsafe_allow_html=True)
    returns_model_label = st.selectbox(
        "Returns Model", list(RETURN_MODELS.keys()), index=0, label_visibility="collapsed",
    )
    returns_model = RETURN_MODELS[returns_model_label]

    rc1, rc2 = st.columns(2, vertical_alignment="bottom")
    with rc1:
        st.markdown("<div class='qv-label'>Lookback</div>", unsafe_allow_html=True)
        lookback = st.selectbox(
            "Lookback", [1, 2, 3, 5, 10], index=4,
            format_func=lambda x: f"{x}Y", label_visibility="collapsed",
        )
    with rc2:
        st.markdown("<div class='qv-label'>Base Currency</div>", unsafe_allow_html=True)
        base_currency = st.selectbox(
            "Currency", CURRENCIES, index=0, label_visibility="collapsed",
        )

    st.markdown("<div class='qv-label'>Risk-Free Rate</div>", unsafe_allow_html=True)
    rfr_pct = st.slider(
        "RFR", 0.0, 10.0, RISK_FREE_RATE * 100, 0.5,
        format="%.1f%%", label_visibility="collapsed",
    )
    rfr = rfr_pct / 100

    st.markdown("<div class='qv-label'>Weight Constraints</div>", unsafe_allow_html=True)
    wc1, wc2 = st.columns(2)
    with wc1:
        st.caption("Min per position")
        w_min_pct = st.slider("w_min", 0, 25, 0, 1,
                              format="%d%%", label_visibility="collapsed")
        w_min = w_min_pct / 100
    with wc2:
        st.caption("Max per position")
        w_max_pct = st.slider("w_max", 10, 100, 100, 5,
                              format="%d%%", label_visibility="collapsed")
        w_max = w_max_pct / 100

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    _computing = st.session_state.get("_computing", False)
    run = st.button(
        "⏳  COMPUTING..." if _computing else "▶  RUN OPTIMIZATION",
        disabled=_computing,
    )

    # ── Saved Portfolios ───────────────────────────────────────────────────────
    st.markdown("---")
    n_saved = len(st.session_state.saved_portfolios)
    saved_label = f"SAVED PORTFOLIOS ({n_saved})" if n_saved else "SAVED PORTFOLIOS"
    with st.expander(saved_label, expanded=n_saved > 0):
        sv1, sv2 = st.columns([3, 1])
        with sv1:
            save_name = st.text_input(
                "save_name", placeholder="Portfolio name…",
                label_visibility="collapsed", key="save_name_input",
            )
        with sv2:
            if st.button("SAVE", key="btn_save", use_container_width=True):
                name = save_name.strip()
                if name:
                    st.session_state.saved_portfolios[name] = ticker_input
                    st.success(f"Saved '{name}'")

        if st.session_state.saved_portfolios:
            for pname in list(st.session_state.saved_portfolios):
                lc1, lc2, lc3 = st.columns([4, 2, 1])
                with lc1:
                    st.markdown(
                        f"<div style='color:{TEXT};font-size:.62rem;padding-top:6px;'>{pname}</div>",
                        unsafe_allow_html=True,
                    )
                with lc2:
                    if st.button("LOAD", key=f"load_{pname}"):
                        st.session_state["ticker_input"] = st.session_state.saved_portfolios[pname]
                        st.rerun()
                with lc3:
                    if st.button("DEL", key=f"del_{pname}"):
                        del st.session_state.saved_portfolios[pname]
                        st.rerun()
            json_export = json.dumps(st.session_state.saved_portfolios, indent=2)
            st.markdown('<div class="qv-dl">', unsafe_allow_html=True)
            st.download_button(
                "↓ EXPORT SAVED",
                data=json_export,
                file_name="quant_view_portfolios.json",
                mime="application/json",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<div style='color:#f5a623;font-size:.75rem;letter-spacing:.06em;'>"
        "◈ v2.2 · CVXPY · CLARABEL · LEDOIT-WOLF</div>",
        unsafe_allow_html=True,
    )

# ── Top header bar ─────────────────────────────────────────────────────────────
now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")
st.markdown(
    f"<div style='display:flex;justify-content:space-between;align-items:center;"
    f"border-bottom:2px solid {ACCENT};padding-bottom:8px;margin-bottom:12px;'>"
    f"<div>"
    f"<span style='color:{ACCENT};font-size:1.25rem;font-weight:700;"
    f"letter-spacing:.1em;'>◈ STOCKSBRO</span>"
    f"<span style='color:#9aabb8;font-size:.75rem;letter-spacing:.08em;"
    f"margin-left:14px;'>PROFESSIONAL PORTFOLIO ANALYTICS · MPT ENGINE v2.2</span>"
    f"</div>"
    f"<div style='text-align:right;'>"
    f"<span style='color:{ACCENT};font-size:.8rem;font-weight:600;'>{now_utc}</span><br>"
    f"<span style='color:#9aabb8;font-size:.75rem;'>"
    f"MAX SHARPE · MIN VOL · EFFICIENT FRONTIER · MONTE CARLO · BLACK-LITTERMAN</span>"
    f"</div></div>",
    unsafe_allow_html=True,
)

# ── Run optimization ───────────────────────────────────────────────────────────
if run:
    tickers = [t.strip().upper() for t in ticker_input.splitlines() if t.strip()]
    if len(tickers) < 2:
        st.error("Enter at least 2 tickers.")
        st.stop()
    st.session_state["_computing"] = True
    st.session_state.result = None
    st.session_state["result_params"] = None
    try:
        with st.status("◈ Computing portfolio...", expanded=True) as _status:
            _status.write(f"[1/4] Fetching {len(tickers)} tickers from Yahoo Finance...")
            result = _run_opt(
                tuple(tickers), strategy, rfr, lookback, w_min, w_max,
                returns_model, base_currency,
            )
            _status.write(f"[2/4] Covariance estimated — Ledoit-Wolf shrinkage ({returns_model_label})")
            _status.write("[3/4] Efficient frontier solved — CVXPY · CLARABEL")
            _status.write("[4/4] Fetching company names...")
            active_tks = tuple(t for t, w in result["weights"].items() if w > 0.0001)
            company_names = _get_names(active_tks)
            _status.update(label="◈ Portfolio optimized  ✓", state="complete", expanded=False)
        st.session_state.result = result
        st.session_state.company_names = company_names
        st.session_state["result_params"] = {
            "tickers": tuple(sorted(tickers)),
            "strategy": strategy,
            "rfr": rfr,
            "lookback": lookback,
            "w_min": w_min,
            "w_max": w_max,
            "returns_model": returns_model,
            "base_currency": base_currency,
        }
    except Exception as e:
        st.error(f"Optimization failed: {e}")
    finally:
        st.session_state["_computing"] = False

# ── Stale-result warning ───────────────────────────────────────────────────────
if st.session_state.result is not None and st.session_state.get("result_params"):
    rp = st.session_state["result_params"]
    current_tickers = tuple(sorted([t.strip().upper() for t in ticker_input.splitlines() if t.strip()]))
    params_changed = (
        current_tickers != rp["tickers"]
        or strategy != rp["strategy"]
        or rfr != rp["rfr"]
        or lookback != rp["lookback"]
        or w_min != rp["w_min"]
        or w_max != rp["w_max"]
        or returns_model != rp["returns_model"]
        or base_currency != rp["base_currency"]
    )
    if params_changed:
        st.warning("Parameters changed — press **RUN OPTIMIZATION** to refresh results.", icon="⚠️")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "OPTIMIZER",
    "ANALYTICS",
    "BACKTEST",
    "HOLDINGS",
    "GUIDE",
])

with tab1:
    if st.session_state.result is None:
        landing("CONFIGURE PORTFOLIO IN SIDEBAR · PRESS RUN OPTIMIZATION")
    else:
        render_optimizer(
            st.session_state.result,
            strategy_label,
            st.session_state.company_names,
        )

with tab2:
    if st.session_state.result is None:
        landing("RUN OPTIMIZATION FIRST TO VIEW ANALYTICS")
    else:
        render_analytics(st.session_state.result, _run_ef, _run_stats, _run_mc)

with tab3:
    if st.session_state.result is None:
        landing("RUN OPTIMIZATION FIRST TO VIEW BACKTEST")
    else:
        render_backtest(st.session_state.result, _run_bt)

with tab4:
    if st.session_state.result is None:
        landing("RUN OPTIMIZATION FIRST TO VIEW HOLDINGS")
    else:
        render_holdings(st.session_state.result, _run_stats, _run_rb)

with tab5:
    render_guide()

# ── Tab state persistence (survives Streamlit reruns) ─────────────────────────
components.html("""<script>
(function(){
  var KEY='sb_tab';
  function save(i){try{localStorage.setItem(KEY,String(i));}catch(e){}}
  function bind(){
    var tabs=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
    tabs.forEach(function(t,i){
      if(!t._sbBound){t._sbBound=true;t.addEventListener('click',function(){save(i);});}
    });
  }
  function restore(){
    var s=localStorage.getItem(KEY);
    if(!s||s==='0'){bind();return;}
    var tabs=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
    var idx=parseInt(s,10);
    if(tabs.length>idx){tabs[idx].click();}
    bind();
  }
  setTimeout(restore,180);
})();
</script>""", height=0)
