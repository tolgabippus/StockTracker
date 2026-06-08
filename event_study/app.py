"""
app.py — Globaler Marktvergleich & Einzelaktien

Start:
    streamlit run app.py
"""

import importlib
import io
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

try:
    from openai import OpenAI as _OpenAI
    _OPENAI_OK = True
except ImportError:
    _OpenAI = None
    _OPENAI_OK = False

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

import data.constituents as _constituents_mod
from data.constituents import STOXX50_TICKERS

ROOT              = Path(__file__).resolve().parent
_FULL_JSON        = ROOT / "data" / "stoxx600_full_tickers.json"
_SCORES_PATH      = ROOT / "data" / "russia_scores.json"
_SCREENING_PATH   = ROOT / "data" / "screening_results.json"


def _get_stoxx600() -> list[str]:
    if _FULL_JSON.exists():
        return json.loads(_FULL_JSON.read_text())["tickers"]
    importlib.reload(_constituents_mod)
    return _constituents_mod.STOXX600_TICKERS


STOXX600_TICKERS = _get_stoxx600()

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marktvergleich",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; }

html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI",
                 Helvetica, Arial, sans-serif !important;
}

/* ── App background ── */
.stApp { background-color: #FFFFFF !important; }
.stApp > header { background-color: transparent !important; }

/* ── Hide chrome ── */
#MainMenu, footer                  { visibility: hidden !important; }
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stDecoration"]       { display: none !important; }
[data-testid="stStatusWidget"]     { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
    background-color: #F8FAFC !important;
}
[data-testid="stSidebar"] {
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem !important;
}

/* ── Sidebar expand button (appears when sidebar is closed) ── */
[data-testid="collapsedControl"] {
    background: #2563EB !important;
    border-radius: 0 8px 8px 0 !important;
    border: none !important;
    box-shadow: 3px 0 12px rgba(37,99,235,0.25) !important;
    z-index: 999999 !important;
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    min-width: 28px !important;
}
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"] > button {
    background: transparent !important;
    color: #FFFFFF !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="collapsedControl"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    visibility: visible !important;
}
/* Sidebar close button (chevron inside sidebar) */
[data-testid="stSidebarCollapseButton"] button {
    color: #9CA3AF !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    color: #374151 !important;
    background: #F1F5F9 !important;
}

/* ── Sidebar section labels ── */
[data-testid="stSidebar"] h3 {
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    color: #9CA3AF !important;
    margin: 1.4rem 0 0.35rem 0 !important;
    padding: 0 !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-size: 0.8rem !important;
    color: #6B7280 !important;
}

/* ── Main padding ── */
.main .block-container {
    padding-top: 1.75rem !important;
    padding-left: 2.25rem !important;
    padding-right: 2.25rem !important;
    max-width: 1200px !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] {
    margin-top: 0.25rem !important;
}
button[data-baseweb="tab"] {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    padding: 0.5rem 0.1rem !important;
    margin-right: 1.5rem !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}
button[data-baseweb="tab"]:hover {
    color: #374151 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #111827 !important;
    border-bottom: 2px solid #2563EB !important;
    font-weight: 600 !important;
}
[data-testid="stTabsContent"] {
    padding-top: 1.25rem !important;
}

/* ── Typography ── */
h1 { font-size: 1.5rem !important; font-weight: 700 !important;
     color: #111827 !important; letter-spacing: -0.025em !important; }
h2 { font-size: 1rem !important; font-weight: 600 !important; color: #111827 !important; }
h3 { color: #111827 !important; }
p, li, label { color: #374151 !important; }

/* ── Date input ── */
[data-testid="stDateInput"] input {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    color: #111827 !important;
    font-size: 0.84rem !important;
}
[data-testid="stDateInput"] input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label p {
    font-size: 0.84rem !important;
    color: #374151 !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label p {
    font-size: 0.875rem !important;
    color: #374151 !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    color: #111827 !important;
    font-size: 0.875rem !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    font-size: 0.875rem !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 6px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border: 1px solid #D1D5DB !important;
    background-color: #FFFFFF !important;
    color: #374151 !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton > button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background-color: #EFF6FF !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #1D4ED8 !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.25) !important;
}
.stDownloadButton > button:hover {
    background-color: #1D4ED8 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
    background-color: #FAFAFA !important;
    padding: 0.55rem 1rem !important;
}

/* ── Dividers ── */
hr { border: none !important; border-top: 1px solid #F1F5F9 !important; margin: 1rem 0 !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p, .stCaption p {
    font-size: 0.775rem !important;
    color: #9CA3AF !important;
    line-height: 1.6 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.875rem !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] > div {
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid #E5E7EB !important;
}

/* ── Chart card ── */
[data-testid="stPlotlyChart"] > div {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #F1F5F9 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}

/* ── Smooth transitions ── */
.stButton > button,
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stSelectbox"] > div > div {
    transition: all 0.15s ease !important;
}
[data-testid="stCheckbox"]:hover label p { color: #111827 !important; }

/* ── Metric cards ── */
.kpi-card {
    background: #FAFAFA;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    height: 100%;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F9FAFB; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
INDICES: dict[str, dict] = {
    "Euro STOXX 50":                  {"ticker": "^STOXX50E", "region": "Europa",     "note": "Index direkt",                                         "color": "#1E3A8A"},
    "STOXX Europe 600":               {"ticker": "EXSA.DE",   "region": "Europa",     "note": "ETF-Proxy: iShares STOXX Europe 600 UCITS ETF",         "color": "#2563EB"},
    "MSCI EM Eastern Europe ex Russia":{"ticker": "CE9.DE",   "region": "Europa",     "note": "ETF-Proxy: iShares MSCI Eastern Europe Capped",         "color": "#60A5FA"},
    "STOXX Eastern Europe Large 100": {"ticker": "EPOL",      "region": "Europa",     "note": "ETF-Proxy: iShares MSCI Poland ETF",                    "color": "#93C5FD"},
    "MSCI Europe Small Cap":          {"ticker": "IEUS",      "region": "Europa",     "note": "ETF-Proxy: iShares MSCI Europe Small-Cap ETF",          "color": "#BFDBFE"},
    "Dow Jones Industrial":           {"ticker": "^DJI",      "region": "Amerika",    "note": "Index direkt",                                         "color": "#991B1B"},
    "NASDAQ Composite":               {"ticker": "^IXIC",     "region": "Amerika",    "note": "Index direkt",                                         "color": "#EF4444"},
    "S&P Asia 50":                    {"ticker": "AIA",       "region": "Asien",      "note": "ETF-Proxy: iShares S&P Asia 50 ETF",                   "color": "#065F46"},
    "MSCI AC Asia":                   {"ticker": "AAXJ",      "region": "Asien",      "note": "ETF-Proxy: iShares MSCI All Country Asia ex Japan ETF", "color": "#10B981"},
    "MSCI Australia Large Cap":       {"ticker": "EWA",       "region": "Australien", "note": "ETF-Proxy: iShares MSCI Australia ETF",                 "color": "#D97706"},
}

REGIONS    = ["Amerika", "Asien", "Australien", "Europa"]
REGION_COLORS = {
    "Amerika":    "#EF4444",
    "Asien":      "#059669",
    "Australien": "#D97706",
    "Europa":     "#2563EB",
}
EVENT_DATE        = pd.Timestamp("2022-02-24")
EVENT_STR         = "2022-02-24"
_BENCHMARK_TICKER = "EXSA.DE"   # iShares STOXX Europe 600 ETF — market proxy


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def download_prices(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    frames: list[pd.Series] = []
    for ticker in tickers:
        try:
            raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if raw.empty:
                continue
            close = raw["Close"].iloc[:, 0] if isinstance(raw.columns, pd.MultiIndex) else raw["Close"]
            close.name = ticker
            frames.append(close)
        except Exception:
            pass
    return pd.concat(frames, axis=1, sort=True).ffill() if frames else pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def download_batch(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    try:
        raw = yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        return close.ffill()
    except Exception:
        return pd.DataFrame()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    first = df.apply(lambda c: c.dropna().iloc[0] if c.dropna().size else np.nan)
    return df.div(first) * 100


def divider(label: str = "") -> None:
    """Thin section separator with optional label."""
    if label:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.75rem;"
            f"margin:1.75rem 0 0.75rem 0'>"
            f"<div style='font-size:0.78rem;font-weight:600;color:#6B7280;"
            f"text-transform:uppercase;letter-spacing:0.07em;white-space:nowrap'>{label}</div>"
            f"<div style='flex:1;height:1px;background:#F1F5F9'></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div style='height:1px;background:#F1F5F9;margin:1.5rem 0'></div>",
                    unsafe_allow_html=True)


def excel_export_card(
    buf: io.BytesIO,
    fname: str,
    n_items: int,
    start: date,
    end: date,
    sheet_desc: str,
) -> None:
    """Render file info card + download button."""
    _kb = round(len(buf.getvalue()) / 1024)
    st.markdown(
        f"""<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                        padding:0.9rem 1.1rem;margin:0.75rem 0 0.5rem 0;
                        display:flex;align-items:center;gap:0.9rem">
              <div style="flex-shrink:0;width:38px;height:38px;background:#166534;
                          border-radius:7px;display:flex;align-items:center;
                          justify-content:center;font-size:0.55rem;font-weight:800;
                          color:white;letter-spacing:0.03em;line-height:1">XLSX</div>
              <div style="flex:1;min-width:0">
                <div style="font-size:0.84rem;font-weight:600;color:#111827;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{fname}</div>
                <div style="font-size:0.74rem;color:#6B7280;margin-top:3px">
                  {n_items} Einträge &nbsp;·&nbsp;
                  {start.strftime('%d.%m.%Y')} – {end.strftime('%d.%m.%Y')} &nbsp;·&nbsp;
                  {_kb} KB &nbsp;·&nbsp; {sheet_desc}
                </div>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )
    st.download_button(
        label="Excel herunterladen",
        data=buf.getvalue(),
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )


def metric_card(col, label: str, value: float, sub: str) -> None:
    """Render a compact KPI card with colour-coded value."""
    clr = "#16A34A" if value >= 0 else "#DC2626"
    bg  = "#F0FDF4" if value >= 0 else "#FEF2F2"
    with col:
        st.markdown(
            f"<div style='background:{bg};border:1px solid #E5E7EB;"
            f"border-radius:10px;padding:0.85rem 1rem;"
            f"border-left:3px solid {clr}'>"
            f"<div style='font-size:0.62rem;font-weight:700;color:#9CA3AF;"
            f"text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.3rem'>"
            f"{label}</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{clr};"
            f"letter-spacing:-0.02em;line-height:1.1'>{value:+.1%}</div>"
            f"<div style='font-size:0.72rem;color:#6B7280;margin-top:0.3rem;"
            f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{sub}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Thesis-Analyse — Score-Persistenz & AR-Berechnung
# ─────────────────────────────────────────────────────────────────────────────
def load_scores() -> pd.DataFrame:
    """Load Russia exposure scores from JSON file."""
    _str_cols = [
        "Ticker", "Unternehmen", "Sektor", "Confidence",
        "Revenue Evidence", "Revenue Justification",
        "Operational Evidence", "Operational Justification",
        "Audit Trail", "Notizen",
    ]
    _empty = pd.DataFrame({c: pd.Series(dtype=str) for c in _str_cols}
                          | {"Revenue Score": pd.Series(dtype=int),
                             "Operational Score": pd.Series(dtype=int)})
    if not _SCORES_PATH.exists():
        return _empty
    try:
        records = json.loads(_SCORES_PATH.read_text())
        df = pd.DataFrame(records)
        for col in ["Revenue Score", "Operational Score"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        for col in _str_cols:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return _empty


def save_scores(df: pd.DataFrame) -> None:
    """Persist Russia exposure scores to JSON file."""
    _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCORES_PATH.write_text(
        json.dumps(df.to_dict(orient="records"), indent=2, ensure_ascii=False)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pre-Screening helpers
# ─────────────────────────────────────────────────────────────────────────────
_SCREEN_SYS = """\
You are a financial screening assistant. Quickly assess pre-war Russian market exposure for a European large-cap company (before 24 February 2022).

Respond ONLY in this exact machine-readable format — no other text whatsoever:

COMPANY: [full company name]
REVENUE_SCORE: [0|1|2|3]
OPERATIONAL_SCORE: [0|1|2|3]
REASON: [max 15 words explaining key Russia connection, or "No identifiable Russia exposure"]
TICKER: [confirmed yfinance ticker or UNKNOWN]

Scoring:
  Revenue:     0 = <1%   1 = 1-5%   2 = 5-10%   3 = >10% of total revenue from Russia
  Operational: 0 = none  1 = limited 2 = significant  3 = critical presence in Russia

Rules: Conservative scoring — when uncertain score lower. If company is unknown from the ticker, return all scores as 0.\
"""


def load_screening() -> pd.DataFrame:
    _empty = pd.DataFrame({
        "Ticker":    pd.Series(dtype=str),
        "Company":   pd.Series(dtype=str),
        "Rev Score": pd.Series(dtype=object),
        "Op Score":  pd.Series(dtype=object),
        "Reason":    pd.Series(dtype=str),
        "AI Ticker": pd.Series(dtype=str),
    })
    if not _SCREENING_PATH.exists():
        return _empty
    try:
        return pd.DataFrame(json.loads(_SCREENING_PATH.read_text()))
    except Exception:
        return _empty


def save_screening(df: pd.DataFrame) -> None:
    _SCREENING_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCREENING_PATH.write_text(
        json.dumps(df.to_dict(orient="records"), indent=2, ensure_ascii=False)
    )


def run_quick_screen(api_key: str, ticker: str) -> str:
    client = _OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=120,
        temperature=0.0,
        messages=[
            {"role": "system", "content": _SCREEN_SYS},
            {"role": "user", "content": f"Screen company with yfinance ticker: {ticker}"},
        ],
    )
    return resp.choices[0].message.content


def parse_screen_result(text: str, ticker: str) -> dict:
    def _get(pattern, default=""):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    rev = _get(r'REVENUE_SCORE:\s*([0-3])')
    ops = _get(r'OPERATIONAL_SCORE:\s*([0-3])')
    ai_t = _get(r'TICKER:\s*([A-Z0-9][A-Z0-9.\-]{0,19})')
    return {
        "Ticker":    ticker,
        "Company":   _get(r'COMPANY:\s*(.+)'),
        "Rev Score": int(rev) if rev else None,
        "Op Score":  int(ops) if ops else None,
        "Reason":    _get(r'REASON:\s*(.+)'),
        "AI Ticker": ai_t if ai_t and ai_t.upper() != "UNKNOWN" else ticker,
    }


@st.cache_data(show_spinner=False, ttl=3600)
def calc_ar_thesis(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Compute AR/CAR using Mean-Adjusted and Market Model; CAR[-1,+1], [-3,+3], 30-day."""
    all_dl = tuple(dict.fromkeys(list(tickers) + [_BENCHMARK_TICKER]))
    raw = download_batch(all_dl, "2019-06-01", "2022-04-30")
    if raw.empty:
        return pd.DataFrame()

    r_all = np.log(raw / raw.shift(1)).dropna(how="all")
    r_mkt = r_all[_BENCHMARK_TICKER].dropna() if _BENCHMARK_TICKER in r_all.columns else None

    def _get_win(series: pd.Series, off_s: int, off_e: int) -> pd.Series:
        """Slice [off_s, off_e] trading-day offsets around EVENT_DATE."""
        on_or_after = series.index[series.index >= EVENT_DATE]
        if len(on_or_after) == 0:
            return pd.Series(dtype=float)
        ep = series.index.get_loc(on_or_after[0])
        s, e = max(0, ep + off_s), min(len(series), ep + off_e + 1)
        return series.iloc[s:e] if s < e else pd.Series(dtype=float)

    rows = []
    for ticker in tickers:
        if ticker not in r_all.columns:
            continue
        r_i = r_all[ticker].dropna()
        if len(r_i) < 40:
            continue

        # Estimation window: up to 120 obs, ending 11 calendar days before event
        pre_idx = r_i.index[r_i.index < EVENT_DATE - pd.Timedelta(days=11)]
        if len(pre_idx) < 30:
            continue
        est_idx  = pre_idx[-120:]
        r_i_est  = r_i.loc[est_idx]
        mu_ma    = float(r_i_est.mean())
        sigma_ma = float(r_i_est.std(ddof=1)) if len(r_i_est) > 1 else np.nan

        # Market-Model OLS: R_i = α + β·R_m + ε
        alpha_mm = beta_mm = sigma_mm = np.nan
        if r_mkt is not None:
            rm_est = r_mkt.reindex(est_idx).dropna()
            ri_est = r_i_est.reindex(rm_est.index).dropna()
            rm_est = rm_est.loc[ri_est.index]
            if len(ri_est) >= 20:
                X = np.column_stack([np.ones(len(rm_est)), rm_est.values])
                c, *_ = np.linalg.lstsq(X, ri_est.values, rcond=None)
                alpha_mm, beta_mm = float(c[0]), float(c[1])
                resid    = ri_est.values - (alpha_mm + beta_mm * rm_est.values)
                sigma_mm = float(np.std(resid, ddof=2)) if len(resid) > 2 else np.nan

        def _car(off_s: int, off_e: int, model: str) -> tuple[float, float]:
            win = _get_win(r_i, off_s, off_e)
            if win.empty:
                return np.nan, np.nan
            ars = []
            for d, ri in win.items():
                if model == "ma":
                    ars.append(ri - mu_ma)
                elif r_mkt is not None and d in r_mkt.index and not np.isnan(beta_mm):
                    ars.append(ri - (alpha_mm + beta_mm * float(r_mkt.loc[d])))
            if not ars:
                return np.nan, np.nan
            car = float(sum(ars))
            sig = sigma_ma if model == "ma" else sigma_mm
            t   = car / (sig * np.sqrt(len(ars))) if (sig and sig > 0) else np.nan
            return car, t

        # Single event-day return (day 0)
        w0   = _get_win(r_i, 0, 0)
        r_ev = float(w0.iloc[0]) if not w0.empty else np.nan
        d0   = w0.index[0] if not w0.empty else None

        ar_ma  = (r_ev - mu_ma)                                                      if not np.isnan(r_ev) else np.nan
        z_ma   = (ar_ma / sigma_ma)                                                  if (sigma_ma and not np.isnan(ar_ma)) else np.nan
        ar_mm  = r_ev - (alpha_mm + beta_mm * float(r_mkt.loc[d0]))                 if (d0 and r_mkt is not None and d0 in r_mkt.index and not np.isnan(beta_mm)) else np.nan
        z_mm   = (ar_mm / sigma_mm)                                                  if (sigma_mm and not np.isnan(ar_mm)) else np.nan

        car_11_ma, t_11_ma = _car(-1, 1, "ma")
        car_33_ma, t_33_ma = _car(-3, 3, "ma")
        car_11_mm, t_11_mm = _car(-1, 1, "mm")
        car_33_mm, t_33_mm = _car(-3, 3, "mm")

        # 30-day post-event (~21 trading days)
        w30      = _get_win(r_i, 0, 20)
        cr_30    = float(w30.sum())                                        if not w30.empty else np.nan
        bhar_30  = float(np.prod(1 + w30.values) - 1)                     if not w30.empty else np.nan
        bhar_abn = np.nan
        if r_mkt is not None and not w30.empty:
            rm30 = r_mkt.reindex(w30.index).dropna()
            if len(rm30) > 0:
                bhar_abn = bhar_30 - float(np.prod(1 + rm30.values) - 1)

        rows.append({
            "Ticker":        ticker,
            # backward-compat single-day
            "AR":            ar_ma,
            "Z-Score":       z_ma,
            "Return 24.02.": r_ev,
            # single-day market model
            "AR_mm":         ar_mm,
            "Z_mm":          z_mm,
            # CAR mean-adjusted
            "CAR[-1,+1]":    car_11_ma,
            "t[-1,+1]":      t_11_ma,
            "CAR[-3,+3]":    car_33_ma,
            "t[-3,+3]":      t_33_ma,
            # CAR market model
            "CAR[-1,+1]_mm": car_11_mm,
            "t[-1,+1]_mm":   t_11_mm,
            "CAR[-3,+3]_mm": car_33_mm,
            "t[-3,+3]_mm":   t_33_mm,
            # 30-day
            "CR_30d":        cr_30,
            "BHAR_30d":      bhar_abn,
            # model params
            "alpha":         alpha_mm,
            "beta":          beta_mm,
        })

    return pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()


def parse_russia_scores(text: str) -> dict:
    """Extract all structured fields from AI response."""
    # Core scores from machine-readable block
    rev  = re.search(r'REVENUE_SCORE:\s*([0-3])', text)
    ops  = re.search(r'OPERATIONAL_SCORE:\s*([0-3])', text)
    conf = re.search(r'CONFIDENCE:\s*(High|Medium|Low)', text, re.IGNORECASE)
    tkr  = re.search(r'TICKER:\s*([A-Z0-9][A-Z0-9\.\-]{0,19})', text)
    # Fallbacks from table
    if not rev:
        rev = re.search(r'Revenue Exposure Score[^\d]*([0-3])', text)
    if not ops:
        ops = re.search(r'Operational Exposure Score[^\d]*([0-3])', text)

    _ticker = None
    if tkr:
        _t = tkr.group(1).strip()
        if _t.upper() != "UNKNOWN":
            _ticker = _t

    # Extract narrative sections (between ### headings)
    def _section(heading: str) -> str:
        m = re.search(
            r'###\s*' + re.escape(heading) + r'\s*\n(.*?)(?=\n###|\Z)',
            text, re.DOTALL | re.IGNORECASE,
        )
        return m.group(1).strip() if m else ""

    # Extract evidence from summary table rows
    def _table_field(label: str) -> str:
        m = re.search(r'\|\s*' + re.escape(label) + r'\s*\|\s*(.*?)\s*\|', text)
        return m.group(1).strip() if m else ""

    return {
        "revenue_score":              int(rev.group(1))           if rev   else None,
        "operational_score":          int(ops.group(1))           if ops   else None,
        "confidence":                 conf.group(1).capitalize()  if conf  else None,
        "ticker":                     _ticker,
        "revenue_evidence":           _table_field("Revenue Exposure Evidence"),
        "revenue_justification":      _section("Revenue Exposure Justification"),
        "operational_evidence":       _table_field("Operational Exposure Evidence"),
        "operational_justification":  _section("Operational Exposure Justification"),
        "audit_trail":                _section("Audit Trail"),
        "methodology_notes":          _section("Methodology Notes"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Russland-Analyse — Systemprompt & API-Wrapper
# ─────────────────────────────────────────────────────────────────────────────
_RUSSIA_SYS = """\
You are an academic research assistant for a bachelor thesis:
"How did 2022 EU/US sanctions against Russia affect stock market valuations of STOXX Europe 600 firms with different Russian exposure?"

Assess each company's PRE-WAR Russian exposure (before 24 February 2022) using annual reports, investor presentations, regulatory filings, press releases, and reputable financial databases.

======================================================================
REVENUE EXPOSURE SCORE
======================================================================
Measure: Russian Revenue / Total Revenue

  0 = No exposure or < 1% of total revenue
  1 = Low:       ~1–5% of total revenue
  2 = Moderate:  ~5–10% of total revenue
  3 = High:      > 10% of total revenue

If exact figures are unavailable, estimate conservatively with qualitative evidence.

Generate:
  • Revenue Exposure Score (0/1/2/3)
  • Revenue Exposure Evidence (key facts + sources, 1–3 sentences)
  • Revenue Exposure Justification (50–150 words):
      – why this score was assigned
      – why a HIGHER score was NOT assigned
      – why a LOWER score was NOT assigned

======================================================================
OPERATIONAL EXPOSURE SCORE
======================================================================
Evaluate these subdimensions:
  1. Subsidiaries / legal entities in Russia
  2. Production facilities
  3. Employees in Russia
  4. Retail presence / distribution networks
  5. Joint ventures
  6. Physical assets
  7. Supply-chain dependence on Russia
  8. Strategic importance of Russia for the business model

  0 = No operational presence
  1 = Limited  (sales offices, small subs, minor distribution)
  2 = Significant (multiple subs, relevant local ops, meaningful employees/assets)
  3 = Critical  (major production, large workforce, strategic JVs, heavy supply-chain dependence)

Do NOT create separate scores for Asset Exposure, Supply Chain, or Strategic Importance.
Use them as subdimensions of the single Operational Exposure Score.

Generate:
  • Operational Exposure Score (0/1/2/3)
  • Operational Exposure Evidence (key facts + sources, 1–3 sentences)
  • Operational Exposure Justification (50–150 words):
      – which subdimensions contributed most
      – why this score was assigned
      – why a HIGHER score was NOT assigned
      – why a LOWER score was NOT assigned

======================================================================
AUDIT TRAIL
======================================================================
For EACH score, list every source used. Format each entry exactly as:

**Source:** [document name, year, page/URL if known]
**Evidence:** "[exact quote or precise paraphrase]"
**Interpretation:** [how this evidence influenced the score]
**Score Impact:** Revenue Score = X | Operational Score = X

======================================================================
QUALITY RULES
======================================================================
• Use ONLY information available before or immediately after 24 February 2022
• Conservative scoring when evidence is ambiguous
• Mark all inferences as [ESTIMATE] or [INFERRED]
• Never assign scores without justification
• Do NOT use post-war divestment as primary evidence of pre-war exposure
• Do NOT conflate Eastern Europe / CIS / "international" with Russia unless
  Russia is explicitly identified

======================================================================
OUTPUT FORMAT (use this structure exactly)
======================================================================

## [Company Name]

### Summary Table
| Field | Content |
|---|---|
| Company Name | ... |
| Ticker | [yfinance ticker, e.g. RNO.PA, VOW3.DE, BP.L, NESN.SW] |
| Country | ... |
| Sector (GICS) | ... |
| Revenue Exposure Score | 0 / 1 / 2 / 3 |
| Revenue Exposure Evidence | ... |
| Operational Exposure Score | 0 / 1 / 2 / 3 |
| Operational Exposure Evidence | ... |
| Confidence Level | High / Medium / Low |
| Sources | ... |
| Notes | ... |

### Revenue Exposure Justification
[50–150 words]

### Operational Exposure Justification
[50–150 words]

### Audit Trail
[structured audit entries as described above]

### Methodology Notes
[caveats, data limitations, inference flags]

IMPORTANT — append this block verbatim at the very end (required for automated processing — never skip or modify the format):

```scores
REVENUE_SCORE: [0|1|2|3]
OPERATIONAL_SCORE: [0|1|2|3]
CONFIDENCE: [High|Medium|Low]
TICKER: [yfinance ticker for primary listing — if genuinely unknown write UNKNOWN]
```\
"""


def run_russia_analysis(api_key: str, company: str) -> str:
    """Call DeepSeek API to assess pre-war Russian exposure of a company."""
    client = _OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=8192,
        temperature=0.1,
        messages=[
            {"role": "system", "content": _RUSSIA_SYS},
            {
                "role": "user",
                "content": (
                    f"Assess the PRE-WAR Russian exposure of: **{company}**\n\n"
                    "Use ONLY information publicly available before 24 February 2022."
                ),
            },
        ],
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — nur Zeitraum & Darstellung
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='margin-bottom:1.25rem'>"
        "<div style='font-size:1rem;font-weight:700;color:#111827;letter-spacing:-0.02em'>"
        "Marktvergleich</div>"
        "<div style='font-size:0.75rem;color:#9CA3AF;margin-top:2px'>"
        "Russland-Ukraine-Krieg · Feb 2022</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1px;background:#E2E8F0;margin-bottom:0.5rem'></div>",
                unsafe_allow_html=True)

    st.subheader("Darstellung")
    mode = st.radio("Modus", ["Normiert (Basis 100)", "Absolut"],
                    horizontal=True, label_visibility="collapsed")
    show_event = st.checkbox("Kriegsbeginn markieren", value=True)

    st.markdown("<div style='height:1px;background:#E2E8F0;margin-top:2rem;margin-bottom:0.5rem'></div>",
                unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.72rem;color:#C4C9D4'>Kursdaten: Yahoo Finance</div>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Page header — title left · date range right (always visible)
# ─────────────────────────────────────────────────────────────────────────────
_hdr_l, _hdr_r = st.columns([3, 2])
with _hdr_l:
    st.markdown(
        "<h1 style='margin-bottom:0;margin-top:0.15rem'>Globaler Marktvergleich</h1>"
        "<p style='font-size:0.84rem;color:#9CA3AF;margin:2px 0 0.75rem 0'>"
        "Russland-Ukraine-Krieg &nbsp;·&nbsp; Feb 2022</p>",
        unsafe_allow_html=True,
    )
with _hdr_r:
    _dc1, _dc2 = st.columns(2)
    with _dc1:
        start_date = st.date_input("Von", value=date(2021, 1, 1), label_visibility="visible")
    with _dc2:
        end_date = st.date_input("Bis", value=date.today(), label_visibility="visible")

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_markt, tab_aktien, tab_screen, tab_russia, tab_thesis = st.tabs(
    ["Indizes", "Einzelaktien", "Pre-Screening", "Russland-Analyse", "Thesis-Analyse"]
)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKTVERGLEICH
# ═════════════════════════════════════════════════════════════════════════════
with tab_markt:

    # ── Index-Auswahl: gewichtete Spalten nach Anzahl Einträge ──────────────
    # Amerika 2, Asien 2, Australien 1, Europa 5  →  Proportionen 2:2:1:4
    selected_names: list[str] = []
    _region_weights = {"Amerika": 2, "Asien": 2, "Australien": 1.5, "Europa": 4}
    _col_weights = [_region_weights[r] for r in REGIONS]
    region_cols = st.columns(_col_weights)
    for col, region in zip(region_cols, REGIONS):
        with col:
            _rc = REGION_COLORS[region]
            st.markdown(
                f"<div style='font-size:0.67rem;font-weight:700;color:{_rc};"
                f"text-transform:uppercase;letter-spacing:0.08em;"
                f"margin:0 0 0.5rem 0;border-bottom:2px solid {_rc}30;"
                f"padding-bottom:0.35rem;"
                f"display:flex;align-items:center;gap:6px'>"
                f"<span style='display:inline-block;width:6px;height:6px;"
                f"border-radius:50%;background:{_rc};flex-shrink:0'></span>"
                f"{region}</div>",
                unsafe_allow_html=True,
            )
            for name, meta in INDICES.items():
                if meta["region"] != region:
                    continue
                if st.checkbox(name, value=True, key=f"cb_{name}"):
                    selected_names.append(name)

    if not selected_names:
        st.info("Bitte mindestens einen Index auswählen.")
        st.stop()

    # ── Daten laden ─────────────────────────────────────────────────────────
    with st.spinner("Kursdaten werden geladen ..."):
        prices_raw = download_prices(
            tickers=tuple(INDICES[n]["ticker"] for n in selected_names),
            start=str(start_date), end=str(end_date),
        )

    if prices_raw.empty:
        st.error("Keine Kursdaten verfügbar. Bitte Internetverbindung prüfen.")
        st.stop()

    ticker_to_name = {INDICES[n]["ticker"]: n for n in selected_names}
    available = [
        n for n in selected_names
        if INDICES[n]["ticker"] in prices_raw.columns
        and prices_raw[INDICES[n]["ticker"]].dropna().size > 10
    ]
    missing = [n for n in selected_names if n not in available]
    if missing:
        st.warning(f"Keine Daten: {', '.join(missing)}")

    prices = prices_raw[[INDICES[n]["ticker"] for n in available]].copy()
    prices.columns = [ticker_to_name[c] for c in prices.columns]
    prices = prices.loc[str(start_date):str(end_date)]
    plot_data = normalize(prices) if mode == "Normiert (Basis 100)" else prices

    # ── KPI Cards ────────────────────────────────────────────────────────────
    _perfs_kpi = {
        n: (prices[n].dropna().iloc[-1] / prices[n].dropna().iloc[0] - 1)
        for n in available if prices[n].dropna().size >= 2
    }
    if len(_perfs_kpi) >= 2:
        _best_n  = max(_perfs_kpi, key=_perfs_kpi.get)
        _worst_n = min(_perfs_kpi, key=_perfs_kpi.get)
        _avg_kpi = sum(_perfs_kpi.values()) / len(_perfs_kpi)
        _kc1, _kc2, _kc3 = st.columns(3)
        metric_card(_kc1, "Bestes Ergebnis",      _perfs_kpi[_best_n],  _best_n)
        metric_card(_kc2, "Schwächstes Ergebnis", _perfs_kpi[_worst_n], _worst_n)
        metric_card(_kc3, "Durchschnitt",          _avg_kpi,
                    f"{len(_perfs_kpi)} Indizes · {mode}")
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    # ── Chart ────────────────────────────────────────────────────────────────
    divider()
    fig = go.Figure()
    for name in available:
        meta = INDICES[name]
        y = plot_data[name].dropna()
        fig.add_trace(go.Scatter(
            x=y.index, y=y.values, name=name, mode="lines",
            line=dict(color=meta["color"], width=2,
                      dash="dot" if meta["note"].startswith("ETF") else "solid"),
            hovertemplate=(
                f"<b>{name}</b><br>%{{x|%d.%m.%Y}}<br>"
                + ("%{y:.1f}" if "Normiert" in mode else "%{y:,.0f}")
                + "<extra></extra>"
            ),
        ))

    if show_event and pd.Timestamp(start_date) <= EVENT_DATE <= pd.Timestamp(end_date):
        fig.add_shape(type="line", x0=EVENT_STR, x1=EVENT_STR, y0=0, y1=1,
                      xref="x", yref="paper",
                      line=dict(color="#EF4444", width=1.2, dash="dash"))
        fig.add_annotation(
            x=EVENT_STR, y=0.97, xref="x", yref="paper",
            text="Kriegsbeginn<br>24.02.2022", showarrow=False,
            font=dict(size=10, color="#EF4444"),
            bgcolor="rgba(255,255,255,0.9)", bordercolor="#EF4444",
            borderwidth=1, borderpad=4, xanchor="left",
        )

    fig.update_layout(
        height=480, margin=dict(l=0, r=0, t=10, b=0),
        hovermode="closest",
        legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", xanchor="left",
                    font=dict(size=11, color="#374151"), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6", tickformat="%b %Y",
                   tickfont=dict(size=11, color="#6B7280"), zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6",
                   tickformat=".0f" if "Normiert" in mode else ",.0f",
                   tickfont=dict(size=11, color="#6B7280"),
                   title=dict(text="Basis 100" if "Normiert" in mode else "Kurs",
                              font=dict(size=11, color="#9CA3AF")),
                   zeroline=False),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Performance-Tabelle ──────────────────────────────────────────────────
    divider("Performance")
    war_in_range = pd.Timestamp(end_date) >= EVENT_DATE
    rows = []
    for name in available:
        col = prices[name].dropna()
        if len(col) < 2:
            continue
        nearest = col.index[col.index >= EVENT_DATE]
        rows.append({
            "Index":           name,
            "Region":          INDICES[name]["region"],
            "Performance":     col.iloc[-1] / col.iloc[0] - 1,
            "Seit 24.02.2022": (col.iloc[-1] / col.loc[nearest[0]] - 1) if len(nearest) else np.nan,
            "Typ":             "Direkt" if INDICES[name]["note"] == "Index direkt" else "ETF-Proxy",
        })

    if rows:
        df_perf = pd.DataFrame(rows).set_index("Index")
        if not war_in_range:
            df_perf = df_perf.drop(columns=["Seit 24.02.2022"])
        fmt  = {"Performance": "{:+.1%}"}
        grad = ["Performance"]
        if war_in_range:
            fmt["Seit 24.02.2022"] = "{:+.1%}"
            grad.append("Seit 24.02.2022")
        st.dataframe(
            df_perf.style.format(fmt, na_rep="—")
                    .background_gradient(subset=grad, cmap="RdYlGn", vmin=-0.5, vmax=0.5),
            use_container_width=True,
            height=38 + len(rows) * 35,
        )

    with st.expander("Datenquellen & Ticker"):
        for name in available:
            meta = INDICES[name]
            st.markdown(f"**{name}** — `{meta['ticker']}` — {meta['note']}")

    # ── Excel-Export (Indizes) ───────────────────────────────────────────────
    divider("Excel-Export")

    xi_a, xi_b, xi_c = st.columns([3, 1, 1])
    with xi_a:
        xi_sel = st.multiselect(
            "Indizes", options=available, default=[],
            placeholder=f"Alle {len(available)} Indizes exportieren",
            label_visibility="collapsed", key="xi_sel",
        )
    with xi_b:
        xi_start = st.date_input("Von", value=start_date, key="xi_s")
    with xi_c:
        xi_end = st.date_input("Bis", value=end_date, key="xi_e")

    xi_names = xi_sel if xi_sel else available
    xi_prices  = prices[xi_names].loc[str(xi_start):str(xi_end)]
    xi_returns = np.log(xi_prices / xi_prices.shift(1)).dropna(how="all")
    xi_perf_rows = []
    for n in xi_names:
        c = xi_prices[n].dropna()
        if len(c) < 2:
            continue
        near = c.index[c.index >= EVENT_DATE]
        xi_perf_rows.append({
            "Index": n, "Region": INDICES[n]["region"],
            "Performance": c.iloc[-1] / c.iloc[0] - 1,
            "Seit 24.02.2022": (c.iloc[-1] / c.loc[near[0]] - 1) if len(near) else np.nan,
            "Typ": "Direkt" if INDICES[n]["note"] == "Index direkt" else "ETF-Proxy",
        })
    xi_df_perf = pd.DataFrame(xi_perf_rows).set_index("Index") if xi_perf_rows else pd.DataFrame()

    xi_buf = io.BytesIO()
    with pd.ExcelWriter(xi_buf, engine="openpyxl") as writer:
        xi_prices.round(4).to_excel(writer, sheet_name="Kurse")
        xi_returns.round(6).to_excel(writer, sheet_name="Renditen")
        if not xi_df_perf.empty:
            xi_df_perf.style.format(
                {"Performance": "{:+.2%}", "Seit 24.02.2022": "{:+.2%}"}, na_rep="—"
            ).to_excel(writer, sheet_name="Performance")

    xi_fname = f"indizes_{xi_start}_{xi_end}.xlsx"
    excel_export_card(xi_buf, xi_fname, len(xi_names), xi_start, xi_end,
                      "3 Sheets: Kurse · Renditen · Performance")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — EINZELAKTIEN
# ═════════════════════════════════════════════════════════════════════════════
with tab_aktien:

    # ── Auswahl & Sortierung ─────────────────────────────────────────────────
    sa, sb = st.columns([4, 1])
    with sa:
        idx_choice = st.radio(
            "Index",
            [f"Euro STOXX 50  ({len(STOXX50_TICKERS)} Aktien)",
             f"STOXX Europe 600  ({len(STOXX600_TICKERS)} Aktien)"],
            horizontal=True, label_visibility="collapsed",
        )
    with sb:
        sort_dir = st.selectbox(
            "Sortierung",
            ["Performance (absteigend)", "Performance (aufsteigend)", "Alphabetisch"],
            label_visibility="collapsed",
        )

    if "STOXX 50" in idx_choice:
        const_tickers = tuple(STOXX50_TICKERS)
        section_label = "Euro STOXX 50"
    else:
        const_tickers = tuple(STOXX600_TICKERS)
        section_label = "STOXX Europe 600"

    # ── STOXX 600: CSV-Upload falls JSON fehlt ───────────────────────────────
    if "STOXX 600" in idx_choice and not _FULL_JSON.exists():
        st.markdown(
            "<div style='background:#FEF9C3;border:1px solid #FDE68A;border-radius:8px;"
            "padding:0.75rem 1rem;margin:0.5rem 0 0.75rem 0'>"
            "<div style='font-size:0.84rem;font-weight:600;color:#92400E;margin-bottom:0.3rem'>"
            "Fallback-Liste aktiv — nur 272 von 600 Aktien verfügbar"
            "</div>"
            "<div style='font-size:0.8rem;color:#78350F;line-height:1.5'>"
            "iShares blockiert automatische Downloads. Einmalig manuell herunterladen:<br>"
            "<b>1.</b> <a href='https://www.ishares.com/uk/individual/en/products/251904/' "
            "target='_blank' style='color:#2563EB'>ishares.com → STOXX Europe 600 ETF</a>"
            " &nbsp;→&nbsp; <i>Download Holdings</i> (CSV)<br>"
            "<b>2.</b> CSV hier hochladen:"
            "</div></div>",
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader("Holdings-CSV", type=["csv"],
                                    label_visibility="collapsed", key="stoxx600_upload")
        if uploaded is not None:
            with st.spinner("Verarbeite CSV ..."):
                try:
                    _text = uploaded.read().decode("utf-8", errors="replace")
                    _df = None
                    for skip in (2, 1, 0):
                        try:
                            _tmp = pd.read_csv(io.StringIO(_text), skiprows=skip)
                            if {"Ticker", "Exchange"}.issubset(set(_tmp.columns)):
                                _df = _tmp
                                break
                        except Exception:
                            continue
                    if _df is None:
                        st.error("CSV konnte nicht geparst werden.")
                    else:
                        _SUFFIX = {
                            "XETR": ".DE", "XFRA": ".F", "XPAR": ".PA", "XAMS": ".AS",
                            "XLON": ".L", "XMIL": ".MI", "XMAD": ".MC", "XSWX": ".SW",
                            "XVTX": ".SW", "XSTO": ".ST", "XCSE": ".CO", "XHEL": ".HE",
                            "XOSL": ".OL", "XBRU": ".BR", "XWBO": ".VI", "XLIS": ".LS",
                            "XDUB": ".IR", "XWAR": ".WA", "XLUX": ".LU", "ASEX": ".AT",
                        }
                        ticker_col   = next((c for c in _df.columns if "ticker"   in c.lower()), None)
                        exchange_col = next((c for c in _df.columns if "exchange" in c.lower()), None)
                        asset_col    = next((c for c in _df.columns if "asset"    in c.lower()
                                             and "class" in c.lower()), None)
                        tickers_parsed = []
                        for _, row in _df.iterrows():
                            if asset_col and str(row.get(asset_col, "")).strip().lower() \
                                    not in ("equity", "aktie", "stock"):
                                continue
                            raw  = str(row[ticker_col]).strip()
                            exch = str(row[exchange_col]).strip().upper()
                            if raw and raw.lower() not in ("nan", "-", ""):
                                tickers_parsed.append((raw + _SUFFIX.get(exch, "")).upper())
                        tickers_parsed = list(dict.fromkeys(tickers_parsed))
                        _FULL_JSON.parent.mkdir(parents=True, exist_ok=True)
                        _FULL_JSON.write_text(json.dumps(
                            {"tickers": tickers_parsed, "count": len(tickers_parsed)}, indent=2))
                        st.cache_data.clear()
                        st.rerun()
                except Exception as exc:
                    st.error(f"Fehler: {exc}")

    # ── Ladebutton ───────────────────────────────────────────────────────────
    load_key = f"loaded_{section_label}"
    if load_key not in st.session_state:
        st.session_state[load_key] = False

    if not st.session_state[load_key]:
        divider()
        st.markdown(
            f"<p style='font-size:0.875rem;color:#6B7280;margin-bottom:0.75rem'>"
            f"{len(const_tickers)} Aktien · Erster Ladevorgang ca. 15–30 Sekunden, "
            f"danach für 1 Stunde gespeichert.</p>",
            unsafe_allow_html=True,
        )
        if st.button("Aktien laden", type="primary"):
            st.session_state[load_key] = True
            st.rerun()

    else:
        with st.spinner(f"Lade {len(const_tickers)} Aktien ..."):
            const_raw = download_batch(const_tickers, str(start_date), str(end_date))

        if const_raw.empty:
            st.warning("Keine Kursdaten geladen.")
        else:
            valid    = [c for c in const_raw.columns if const_raw[c].dropna().size > 10]
            prices_c = const_raw[valid].loc[str(start_date):str(end_date)]
            r_all    = np.log(prices_c / prices_c.shift(1)).dropna(how="all")
            ar_available = pd.Timestamp(start_date) <= EVENT_DATE <= pd.Timestamp(end_date)

            # ── Kennzahlen berechnen ─────────────────────────────────────────
            perf_rows = []
            for ticker in valid:
                col = prices_c[ticker].dropna()
                if len(col) < 2:
                    continue
                nearest = col.index[col.index >= EVENT_DATE]
                perf_war = (col.iloc[-1] / col.loc[nearest[0]] - 1) if len(nearest) else np.nan

                r = r_all[ticker].dropna() if ticker in r_all else pd.Series(dtype=float)
                ev = r.index[(r.index >= EVENT_DATE) &
                             (r.index <= EVENT_DATE + pd.Timedelta(days=4))]
                r_event = float(r.loc[ev[0]]) if len(ev) else np.nan
                pre = r[r.index < EVENT_DATE].tail(60)
                r_mu  = pre.mean() if len(pre) > 10 else np.nan
                r_sig = pre.std(ddof=1) if len(pre) > 10 else np.nan
                ar = (r_event - r_mu) if not (np.isnan(r_event) or np.isnan(r_mu)) else np.nan
                z  = (ar / r_sig) if (r_sig and r_sig > 0 and not np.isnan(ar)) else np.nan

                if np.isnan(z):    signal = "—"
                elif abs(z) > 3:   signal = "Extrem"
                elif abs(z) > 2:   signal = "Signifikant"
                else:              signal = "Normal"

                perf_rows.append({
                    "Ticker":           ticker,
                    "Performance":      col.iloc[-1] / col.iloc[0] - 1,
                    "Seit 24.02.2022":  perf_war,
                    "Return 24.02.22":  r_event,
                    "Abnormale Rendite":ar,
                    "Z-Score":          z,
                    "Signal":           signal,
                })

            if not perf_rows:
                st.warning("Keine auswertbaren Daten.")
            else:
                df_c = pd.DataFrame(perf_rows).set_index("Ticker")
                if   "absteigend"  in sort_dir: df_c = df_c.sort_values("Performance", ascending=False)
                elif "aufsteigend" in sort_dir: df_c = df_c.sort_values("Performance", ascending=True)
                else:                           df_c = df_c.sort_index()

                # ── KPI Cards ────────────────────────────────────────────────
                _ea_perfs = df_c["Performance"].dropna()
                if len(_ea_perfs) >= 2:
                    _ea_best_t  = _ea_perfs.idxmax()
                    _ea_worst_t = _ea_perfs.idxmin()
                    _ea_avg     = _ea_perfs.mean()
                    _eac1, _eac2, _eac3 = st.columns(3)
                    metric_card(_eac1, "Bestes Ergebnis",
                                _ea_perfs[_ea_best_t], _ea_best_t)
                    metric_card(_eac2, "Schwächstes Ergebnis",
                                _ea_perfs[_ea_worst_t], _ea_worst_t)
                    metric_card(_eac3, "Durchschnitt",
                                _ea_avg, f"{len(_ea_perfs)} Aktien · {section_label}")
                    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

                # ── Bar chart ────────────────────────────────────────────────
                divider()
                colors_bar = ["#16A34A" if v >= 0 else "#DC2626"
                              for v in df_c["Performance"]]
                fig_c = go.Figure(go.Bar(
                    x=df_c.index, y=df_c["Performance"],
                    marker_color=colors_bar,
                    text=[f"{v:+.1%}" for v in df_c["Performance"]],
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>%{y:+.1%}<extra></extra>",
                ))
                fig_c.add_hline(y=0, line_color="#E5E7EB", line_width=1)
                fig_c.update_layout(
                    height=360, margin=dict(l=0, r=0, t=10, b=0),
                    yaxis=dict(tickformat=".0%", showgrid=True, gridcolor="#F3F4F6",
                               zeroline=False, tickfont=dict(size=10, color="#6B7280")),
                    xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#6B7280")),
                    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False,
                )
                st.plotly_chart(fig_c, use_container_width=True)

                # ── Tabelle ──────────────────────────────────────────────────
                divider("Detailtabelle")
                fmt_c  = {"Performance": "{:+.1%}"}
                grad_c = ["Performance"]
                drops  = []
                if pd.Timestamp(end_date) >= EVENT_DATE:
                    fmt_c["Seit 24.02.2022"] = "{:+.1%}"
                    grad_c.append("Seit 24.02.2022")
                else:
                    drops.append("Seit 24.02.2022")
                if ar_available:
                    fmt_c["Return 24.02.22"]   = "{:+.2%}"
                    fmt_c["Abnormale Rendite"]  = "{:+.2%}"
                    fmt_c["Z-Score"]            = "{:.2f}"
                    grad_c += ["Return 24.02.22", "Abnormale Rendite"]
                else:
                    drops += ["Return 24.02.22", "Abnormale Rendite", "Z-Score", "Signal"]

                df_c = df_c.drop(columns=[c for c in drops if c in df_c.columns])
                st.dataframe(
                    df_c.style.format(fmt_c, na_rep="—")
                             .background_gradient(subset=grad_c, cmap="RdYlGn",
                                                  vmin=-0.15, vmax=0.15),
                    use_container_width=True,
                    height=min(38 + len(df_c) * 35, 600),
                )
                if ar_available:
                    st.caption(
                        "Abnormale Rendite = Return am 24.02.22 minus Ø der 60 Handelstage davor. "
                        "Signal: Signifikant |Z| > 2 · Extrem |Z| > 3"
                    )
                st.caption(
                    f"{len(valid)} von {len(const_tickers)} Aktien geladen · "
                    f"{section_label} · {start_date} – {end_date}"
                )

                col_reload, _ = st.columns([1, 4])
                with col_reload:
                    if st.button("Neu laden", key="reload_btn"):
                        st.session_state[load_key] = False
                        st.cache_data.clear()
                        st.rerun()

                # ── Excel-Export (Einzelaktien) ──────────────────────────────
                divider("Excel-Export")

                ea, eb, ec = st.columns([3, 1, 1])
                with ea:
                    export_sel = st.multiselect(
                        "Aktien", options=list(df_c.index), default=[],
                        placeholder=f"Alle {len(df_c)} Aktien exportieren",
                        label_visibility="collapsed",
                    )
                with eb:
                    exp_start = st.date_input("Von", value=start_date, key="exp_s")
                with ec:
                    exp_end   = st.date_input("Bis", value=end_date,   key="exp_e")

                tickers_exp    = export_sel if export_sel else list(df_c.index)
                tickers_exp_ok = [t for t in tickers_exp if t in prices_c.columns]
                prices_exp     = prices_c[tickers_exp_ok].loc[str(exp_start):str(exp_end)]
                returns_exp    = np.log(prices_exp / prices_exp.shift(1)).dropna(how="all")
                perf_exp_rows  = []
                for t in tickers_exp_ok:
                    ct = prices_exp[t].dropna()
                    if len(ct) < 2:
                        continue
                    near = ct.index[ct.index >= EVENT_DATE]
                    perf_exp_rows.append({
                        "Ticker":          t,
                        "Performance":     ct.iloc[-1] / ct.iloc[0] - 1,
                        "Seit 24.02.2022": (ct.iloc[-1] / ct.loc[near[0]] - 1) if len(near) else np.nan,
                    })
                df_exp = (pd.DataFrame(perf_exp_rows).set_index("Ticker")
                          if perf_exp_rows else pd.DataFrame())

                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    prices_exp.round(4).to_excel(writer, sheet_name="Preise")
                    returns_exp.round(6).to_excel(writer, sheet_name="Renditen")
                    if not df_exp.empty:
                        df_exp.style.format(
                            {"Performance": "{:+.2%}", "Seit 24.02.2022": "{:+.2%}"},
                            na_rep="—"
                        ).to_excel(writer, sheet_name="Performance")

                fname = f"stoxx_{section_label.split()[1].lower()}_{exp_start}_{exp_end}.xlsx"
                excel_export_card(buf, fname, len(tickers_exp_ok), exp_start, exp_end,
                                  "3 Sheets: Preise · Renditen · Performance")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — PRE-SCREENING
# ═════════════════════════════════════════════════════════════════════════════
with tab_screen:

    st.markdown(
        "<div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;"
        "padding:0.85rem 1.1rem;margin-bottom:1.25rem'>"
        "<div style='font-size:0.84rem;font-weight:600;color:#166534'>"
        "Phase 1 — Schnell-Screening aller STOXX 600 Unternehmen</div>"
        "<div style='font-size:0.78rem;color:#15803D;margin-top:3px;line-height:1.5'>"
        "Minimale KI-Abfrage (~$0.06 für alle 600) identifiziert Unternehmen mit russischer "
        "Exposition. Nur diese kommen in die vollständige Russland-Analyse (Audit Trail, Justification)."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ── API Key ──────────────────────────────────────────────────────────────
    _sc_env_key = os.environ.get("DEEPSEEK_API_KEY", "") or st.secrets.get("DEEPSEEK_API_KEY", "")
    if not _sc_env_key:
        with st.expander("DeepSeek API Key", expanded=True):
            _sc_key_in = st.text_input("Key", type="password",
                                        placeholder="sk-...", label_visibility="collapsed",
                                        key="sc_key")
        _sc_api_key = _sc_key_in.strip()
    else:
        _sc_api_key = _sc_env_key

    if not _OPENAI_OK or not _sc_api_key:
        st.info("Bitte DeepSeek API Key eingeben.")
        st.stop()

    # ── State & Daten ─────────────────────────────────────────────────────────
    _df_screen = load_screening()
    _done_set  = set(_df_screen["Ticker"].tolist()) if not _df_screen.empty else set()
    _n_total   = len(STOXX600_TICKERS)
    _n_done    = len(_done_set)
    _n_todo    = _n_total - _n_done

    # ── Steuerung ─────────────────────────────────────────────────────────────
    divider("Steuerung")
    _ctrl1, _ctrl2 = st.columns([1, 1])
    with _ctrl1:
        _active = st.session_state.get("screening_active", False)
        if st.button("⏸ Pausieren" if _active else "▶ Starten",
                     type="primary", use_container_width=True, key="screen_toggle"):
            st.session_state["screening_active"] = not _active
            st.rerun()
    with _ctrl2:
        if st.button("Reset", use_container_width=True, key="screen_reset"):
            if _SCREENING_PATH.exists():
                _SCREENING_PATH.unlink()
            st.session_state["screening_active"] = False
            st.rerun()
    _batch_sz = 50

    # Progress
    st.progress(_n_done / _n_total if _n_total else 0)
    st.caption(
        f"{_n_done} / {_n_total} gescreent · {_n_todo} verbleibend · "
        f"Geschätzte Restkosten: ~${_n_todo * 0.0001:.2f}"
    )

    # ── Processing loop ───────────────────────────────────────────────────────
    if st.session_state.get("screening_active") and _n_todo > 0:
        _todo_tickers = [t for t in STOXX600_TICKERS if t not in _done_set]
        _batch        = _todo_tickers[:_batch_sz]
        _status_ph    = st.empty()
        _new_rows     = []

        for _i, _tk in enumerate(_batch):
            _status_ph.markdown(
                f"<span style='font-size:0.8rem;color:#6B7280'>"
                f"Analysiere <b>{_tk}</b> &nbsp;·&nbsp; {_n_done + _i + 1} / {_n_total}</span>",
                unsafe_allow_html=True,
            )
            try:
                _raw = run_quick_screen(_sc_api_key, _tk)
                _row = parse_screen_result(_raw, _tk)
            except Exception as _exc:
                _row = {"Ticker": _tk, "Company": "", "Rev Score": None,
                        "Op Score": None, "Reason": f"Fehler: {_exc}", "AI Ticker": _tk}
            _new_rows.append(_row)
            time.sleep(0.35)   # rate-limit buffer

        _combined = pd.concat([_df_screen, pd.DataFrame(_new_rows)], ignore_index=True)
        save_screening(_combined)
        _status_ph.empty()
        st.rerun()

    elif st.session_state.get("screening_active") and _n_todo == 0:
        st.session_state["screening_active"] = False
        st.success(f"Screening abgeschlossen — {_n_total} Unternehmen gescreent.")

    # ── Ergebnisse ────────────────────────────────────────────────────────────
    if _df_screen.empty:
        st.markdown(
            "<p style='color:#9CA3AF;font-size:0.875rem;margin-top:1rem'>"
            "Noch keine Ergebnisse. Screening starten.</p>",
            unsafe_allow_html=True,
        )
    else:
        # Numeric scores
        _df_sc2 = _df_screen.copy()
        for _c in ["Rev Score", "Op Score"]:
            _df_sc2[_c] = pd.to_numeric(_df_sc2[_c], errors="coerce")
        _df_sc2["Combined"] = _df_sc2["Rev Score"].fillna(0) + _df_sc2["Op Score"].fillna(0)
        _df_sc2["Max Score"] = _df_sc2[["Rev Score", "Op Score"]].max(axis=1)

        # KPI summary
        divider("Überblick")
        _kk1, _kk2, _kk3, _kk4 = st.columns(4)
        _n_any  = int((_df_sc2["Max Score"].fillna(0) >= 1).sum())
        _n_mod  = int((_df_sc2["Max Score"].fillna(0) >= 2).sum())
        _n_high = int((_df_sc2["Max Score"].fillna(0) == 3).sum())
        _kk1.metric("Gescreent",   f"{_n_done} / {_n_total}")
        _kk2.metric("Score ≥ 1",   _n_any,  help="Mindestens geringe Exposition")
        _kk3.metric("Score ≥ 2",   _n_mod,  help="Moderate oder kritische Exposition")
        _kk4.metric("Score = 3",   _n_high, help="Kritische Exposition")

        # Filter
        divider("Ergebnisse filtern")
        _fc1, _fc2 = st.columns([1, 2])
        with _fc1:
            _min_sc = st.selectbox(
                "Mind. Score anzeigen",
                options=[0, 1, 2, 3],
                index=1,
                format_func=lambda x: {0: "Alle", 1: "≥ 1 (gering+)", 2: "≥ 2 (moderat+)", 3: "= 3 (kritisch)"}[x],
                key="sc_min",
            )
        with _fc2:
            _sc_type = st.radio(
                "Basierend auf",
                ["Max Score", "Rev Score", "Op Score", "Combined"],
                horizontal=True, label_visibility="visible", key="sc_type",
            )

        _df_filtered = _df_sc2[_df_sc2[_sc_type].fillna(-1) >= _min_sc].copy()
        _df_display  = (_df_filtered[["Ticker", "Company", "Rev Score", "Op Score",
                                       "Max Score", "Combined", "Reason", "AI Ticker"]]
                        .sort_values("Combined", ascending=False))

        # Score color map for display
        _SC_COLOR_MAP = {0: "#9CA3AF", 1: "#3B82F6", 2: "#F59E0B", 3: "#DC2626"}

        st.dataframe(
            _df_display.style.background_gradient(
                subset=["Rev Score", "Op Score", "Max Score", "Combined"],
                cmap="RdYlGn", vmin=0, vmax=6,
            ).format({"Rev Score": "{:.0f}", "Op Score": "{:.0f}",
                       "Max Score": "{:.0f}", "Combined": "{:.0f}"}, na_rep="—"),
            use_container_width=True,
            height=min(600, 58 + len(_df_display) * 35),
        )
        st.caption(f"{len(_df_filtered)} Unternehmen mit {_sc_type} ≥ {_min_sc}")

        # ── Zur Russland-Analyse hinzufügen ───────────────────────────────────
        divider("Shortlist → Russland-Analyse")
        _exposed   = _df_filtered[_df_filtered["Max Score"].fillna(0) >= 1].copy()
        _t2name    = dict(zip(_exposed["AI Ticker"], _exposed["Company"]))
        if not _exposed.empty:
            _sel = st.multiselect(
                "Unternehmen für vollständige Analyse auswählen",
                options=_exposed["AI Ticker"].tolist(),
                default=[],
                format_func=lambda t: f"{t}  —  {_t2name.get(t, '')}",
                label_visibility="collapsed",
                key="sc_sel",
            )
            _add_col, _info_col = st.columns([2, 3])
            with _add_col:
                if _sel and st.button("Ausgewählte zur Russland-Analyse hinzufügen",
                                       type="primary", use_container_width=True, key="sc_add"):
                    _ex = load_scores()
                    _added = 0
                    for _t in _sel:
                        if _t in _ex["Ticker"].values:
                            continue
                        _r = _exposed[_exposed["AI Ticker"] == _t].iloc[0]
                        _ex = pd.concat([_ex, pd.DataFrame([{
                            "Ticker":                    _t,
                            "Unternehmen":               _r.get("Company", ""),
                            "Sektor":                    "",
                            "Revenue Score":             int(_r["Rev Score"]) if pd.notna(_r["Rev Score"]) else 0,
                            "Revenue Evidence":          "",
                            "Revenue Justification":     "",
                            "Operational Score":         int(_r["Op Score"])  if pd.notna(_r["Op Score"])  else 0,
                            "Operational Evidence":      "",
                            "Operational Justification": "",
                            "Confidence":                "Low",
                            "Audit Trail":               f"Pre-Screening: {_r.get('Reason', '')}",
                            "Notizen":                   "[Pre-Screen only — Vollanalyse ausstehend]",
                        }])], ignore_index=True)
                        _added += 1
                    save_scores(_ex)
                    st.toast(f"{_added} Unternehmen hinzugefügt → Russland-Analyse Tab.", icon="✅")
            with _info_col:
                if _sel:
                    st.caption(
                        f"{len(_sel)} ausgewählt · bereits vorhandene werden übersprungen · "
                        f"Scores als 'Low Confidence' vorbelegt — im Russland-Tab vollständig analysieren"
                    )

        # ── Export ────────────────────────────────────────────────────────────
        divider("Export")
        _sc_buf = io.BytesIO()
        with pd.ExcelWriter(_sc_buf, engine="openpyxl") as _scw:
            _df_sc2.sort_values("Combined", ascending=False).to_excel(
                _scw, sheet_name="Alle Ergebnisse", index=False)
            _df_sc2[_df_sc2["Max Score"].fillna(0) >= 1].sort_values(
                "Combined", ascending=False).to_excel(
                _scw, sheet_name="Shortlist Score≥1", index=False)
        excel_export_card(
            _sc_buf, f"prescreening_{date.today()}.xlsx",
            _n_done, date.today(), date.today(),
            "Alle Ergebnisse · Shortlist Score≥1",
        )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — RUSSLAND-ANALYSE
# ═════════════════════════════════════════════════════════════════════════════
with tab_russia:

    # ── Info-Banner ──────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#FEF3C7;border:1px solid #FDE68A;border-radius:10px;"
        "padding:0.85rem 1.1rem;margin-bottom:1.25rem;display:flex;gap:0.75rem;"
        "align-items:flex-start'>"
        "<div style='font-size:1rem;flex-shrink:0;margin-top:1px'>&#9888;&#65039;</div>"
        "<div>"
        "<div style='font-size:0.84rem;font-weight:600;color:#92400E'>"
        "Vorkriegs-Russland-Exposition &nbsp;·&nbsp; Stichtag: 24. Feb 2022</div>"
        "<div style='font-size:0.78rem;color:#78350F;margin-top:3px;line-height:1.5'>"
        "Analysiert ausschliesslich oeffentlich verfuegbare Informationen VOR Kriegsbeginn "
        "(Geschaeftsberichte 2020/2021, Investorenpresentationen). "
        "Post-War-Effekte, Sanktionen und Unternehmensrueckzuege werden ignoriert."
        "</div></div></div>",
        unsafe_allow_html=True,
    )

    # ── API Key ──────────────────────────────────────────────────────────────
    _env_key = (
        os.environ.get("DEEPSEEK_API_KEY", "")
        or st.secrets.get("DEEPSEEK_API_KEY", "")
    )
    _exp_label = (
        "API Key &nbsp;·&nbsp; aus Umgebungsvariable geladen"
        if _env_key else "DeepSeek API Key einrichten"
    )
    with st.expander(_exp_label, expanded=not bool(_env_key)):
        if not _env_key:
            st.markdown(
                "<div style='font-size:0.8rem;color:#6B7280;margin-bottom:0.6rem'>"
                "Key erstellen unter "
                "<a href='https://platform.deepseek.com/api_keys' target='_blank' "
                "style='color:#2563EB;font-weight:500'>platform.deepseek.com</a> "
                "&nbsp;→&nbsp; API Keys &nbsp;→&nbsp; Create API Key<br>"
                "<span style='color:#9CA3AF'>Kosten: ~$0.001–0.002 pro Analyse (DeepSeek-V3)</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        _key_input = st.text_input(
            "Key",
            type="password",
            placeholder="sk-..." if not _env_key else "(aus DEEPSEEK_API_KEY)",
            label_visibility="collapsed",
            key="ds_key",
        )
    _api_key = _key_input.strip() if _key_input else _env_key

    # ── Pakete / Key prüfen ──────────────────────────────────────────────────
    if not _OPENAI_OK:
        st.error(
            "`openai` Paket nicht installiert. "
            "Bitte `pip install openai` ausfuehren und App neu starten."
        )
    elif not _api_key:
        st.info("Bitte zuerst einen DeepSeek API Key eingeben (siehe oben).")
    else:
        # ── Unternehmensauswahl ──────────────────────────────────────────────
        divider("Unternehmen auswählen")
        _inp_mode = st.radio(
            "Eingabe",
            ["Firmenname eingeben", "Aus STOXX 600 wählen"],
            horizontal=True,
            label_visibility="collapsed",
            key="russia_inp_mode",
        )

        _company_name = ""
        _inp_col, _ = st.columns([3, 2])
        with _inp_col:
            if _inp_mode == "Firmenname eingeben":
                _company_name = st.text_input(
                    "Firmenname",
                    placeholder="z.B. Renault, Volkswagen AG, BASF SE",
                    label_visibility="collapsed",
                    key="russia_company_text",
                )
            else:
                _ticker_sel = st.selectbox(
                    "STOXX 600 Ticker",
                    options=["— bitte wählen —"] + sorted(STOXX600_TICKERS),
                    label_visibility="collapsed",
                    key="russia_ticker_sel",
                )
                if _ticker_sel != "— bitte wählen —":
                    _company_name = _ticker_sel

        # ── Buttons & Analyse ────────────────────────────────────────────────
        if "russia_cache" not in st.session_state:
            st.session_state["russia_cache"] = {}

        _cache_key   = f"russia_{_company_name.strip().lower()}"
        _has_result  = _cache_key in st.session_state["russia_cache"]

        if _company_name:
            _btn_c1, _btn_c2 = st.columns([3, 1])
            with _btn_c1:
                _run = st.button(
                    "Analyse starten", type="primary",
                    use_container_width=True, key="russia_run",
                )
            with _btn_c2:
                if _has_result:
                    if st.button("Neu", use_container_width=True, key="russia_clear"):
                        del st.session_state["russia_cache"][_cache_key]
                        st.rerun()

            if _run:
                try:
                    with st.spinner(
                        f"Analysiere Russland-Exposition von **{_company_name}** …"
                    ):
                        _result = run_russia_analysis(_api_key, _company_name)
                    st.session_state["russia_cache"][_cache_key] = _result
                    st.rerun()
                except Exception as _exc:
                    st.error(f"API-Fehler: {_exc}")

            if _has_result:
                _result     = st.session_state["russia_cache"][_cache_key]
                _parsed     = parse_russia_scores(_result)
                _rev_sc     = _parsed.get("revenue_score")
                _ops_sc     = _parsed.get("operational_score")
                _conf       = _parsed.get("confidence") or ""
                _ai_ticker  = _parsed.get("ticker") or ""
                _eff_ticker = _ai_ticker or (
                    _company_name if _inp_mode != "Firmenname eingeben" else ""
                )

                # ── Event-Study-Metriken ──────────────────────────────────
                _ar_row: dict = {}
                if _eff_ticker:
                    with st.spinner("Berechne CAR/BHAR …"):
                        _ar_df = calc_ar_thesis((_eff_ticker.strip(),))
                    if not _ar_df.empty and _eff_ticker.strip() in _ar_df.index:
                        _ar_row = _ar_df.loc[_eff_ticker.strip()].to_dict()

                # ── KPI-Karten ────────────────────────────────────────────
                _SC_COLOR = {0: "#9CA3AF", 1: "#3B82F6", 2: "#F59E0B", 3: "#DC2626"}
                _SC_DESC  = {0: "< 1 %", 1: "1–5 %", 2: "5–10 %", 3: "> 10 %"}
                _OP_DESC  = {0: "Keine", 1: "Begrenzt", 2: "Signifikant", 3: "Kritisch"}

                def _kpi(label, val, sub, color):
                    return (
                        f"<div style='text-align:center;padding:0.6rem 0.25rem'>"
                        f"<div style='font-size:0.6rem;font-weight:700;color:#9CA3AF;"
                        f"text-transform:uppercase;letter-spacing:0.07em;margin-bottom:5px'>"
                        f"{label}</div>"
                        f"<div style='font-size:1.8rem;font-weight:800;color:{color};"
                        f"line-height:1;letter-spacing:-0.02em'>{val}</div>"
                        f"<div style='font-size:0.7rem;color:#6B7280;margin-top:4px'>{sub}</div>"
                        f"</div>"
                    )

                _cells = ""
                if _rev_sc is not None:
                    _cells += _kpi("Revenue Score", f"{_rev_sc}/3",
                                   _SC_DESC.get(_rev_sc, ""), _SC_COLOR.get(_rev_sc, "#9CA3AF"))
                    _cells += _kpi("Op. Score", f"{(_ops_sc or 0)}/3",
                                   _OP_DESC.get(_ops_sc or 0, ""), _SC_COLOR.get(_ops_sc or 0, "#9CA3AF"))

                _car11 = _ar_row.get("CAR[-1,+1]")
                _car33 = _ar_row.get("CAR[-3,+3]")
                _car11_mm = _ar_row.get("CAR[-1,+1]_mm")
                _t11   = _ar_row.get("t[-1,+1]")
                _bhar  = _ar_row.get("BHAR_30d")

                if _car11 is not None and not np.isnan(_car11):
                    _clr11 = "#16A34A" if _car11 >= 0 else "#DC2626"
                    _sig   = ("Extrem" if abs(_t11) > 3 else "Sign." if abs(_t11) > 2 else "Normal") if (_t11 and not np.isnan(_t11)) else "—"
                    _cells += _kpi("CAR[−1,+1]", f"{_car11*100:+.2f}%", f"Mean-Adj · t={_t11:.2f}" if (_t11 and not np.isnan(_t11)) else "Mean-Adj", _clr11)
                if _car33 is not None and not np.isnan(_car33):
                    _clr33 = "#16A34A" if _car33 >= 0 else "#DC2626"
                    _cells += _kpi("CAR[−3,+3]", f"{_car33*100:+.2f}%", "Mean-Adj", _clr33)
                if _car11_mm is not None and not np.isnan(_car11_mm):
                    _clr_mm = "#16A34A" if _car11_mm >= 0 else "#DC2626"
                    _t11mm = _ar_row.get("t[-1,+1]_mm")
                    _cells += _kpi("CAR[−1,+1]", f"{_car11_mm*100:+.2f}%", f"Mkt-Model · t={_t11mm:.2f}" if (_t11mm and not np.isnan(_t11mm)) else "Mkt-Model", _clr_mm)
                if _bhar is not None and not np.isnan(_bhar):
                    _bclr = "#16A34A" if _bhar >= 0 else "#DC2626"
                    _cells += _kpi("BHAR 30d", f"{_bhar*100:+.2f}%", _eff_ticker, _bclr)
                if _conf:
                    _cells += _kpi("Confidence", _conf, "", "#6B7280")

                if _cells:
                    st.markdown(
                        f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
                        f"border-radius:12px;padding:0.75rem 1rem;margin:0.75rem 0;"
                        f"display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr))'>"
                        f"{_cells}</div>",
                        unsafe_allow_html=True,
                    )

                # ── Justifications & Audit Trail ──────────────────────────
                _rev_just = _parsed.get("revenue_justification", "")
                _ops_just = _parsed.get("operational_justification", "")
                _audit    = _parsed.get("audit_trail", "")
                _meth     = _parsed.get("methodology_notes", "")
                if _rev_just or _ops_just:
                    with st.expander("Justifications (Revenue & Operational)", expanded=False):
                        if _rev_just:
                            st.markdown("**Revenue Exposure Justification**")
                            st.markdown(_rev_just)
                        if _ops_just:
                            st.markdown("**Operational Exposure Justification**")
                            st.markdown(_ops_just)
                if _audit:
                    with st.expander("Audit Trail", expanded=False):
                        st.markdown(_audit)
                if _meth:
                    with st.expander("Methodology Notes", expanded=False):
                        st.markdown(_meth)

                # ── Zur Thesis hinzufügen ─────────────────────────────────
                if _rev_sc is not None:
                    _already = (_eff_ticker and _eff_ticker in load_scores()["Ticker"].values)
                    _thesis_label = "Zur Thesis-Analyse hinzufügen" + (" · bereits vorhanden" if _already else "")
                    if st.button(_thesis_label, type="primary",
                                 use_container_width=False, key="add_thesis"):
                        _df_ex = load_scores()
                        _tk = _eff_ticker or _company_name
                        _new = {
                            "Ticker":                    _tk,
                            "Unternehmen":               _company_name if _inp_mode == "Firmenname eingeben" else "",
                            "Sektor":                    "",
                            "Revenue Score":             _rev_sc,
                            "Revenue Evidence":          _parsed.get("revenue_evidence", ""),
                            "Revenue Justification":     _parsed.get("revenue_justification", ""),
                            "Operational Score":         _ops_sc or 0,
                            "Operational Evidence":      _parsed.get("operational_evidence", ""),
                            "Operational Justification": _parsed.get("operational_justification", ""),
                            "Confidence":                _conf,
                            "Audit Trail":               _parsed.get("audit_trail", ""),
                            "Notizen":                   "",
                        }
                        _mask = _df_ex["Ticker"] == _tk
                        if _mask.any():
                            for _k, _v in _new.items():
                                _df_ex.loc[_mask, _k] = _v
                        else:
                            _df_ex = pd.concat([_df_ex, pd.DataFrame([_new])], ignore_index=True)
                        save_scores(_df_ex)
                        st.toast(f"{_tk} gespeichert.", icon="✅")

                # ── Vollständige Analyse ──────────────────────────────────
                divider(f"Vollständige Analyse: {_company_name}")
                _display_result = re.sub(r'```scores\n.*?```', '', _result, flags=re.DOTALL).strip()
                st.markdown(_display_result)
                divider()
                _dl_col, _ = st.columns([2, 3])
                with _dl_col:
                    st.download_button(
                        label="Analyse herunterladen (.md)",
                        data=_result.encode("utf-8"),
                        file_name=f"russland_analyse_{_company_name.replace(' ', '_').replace('/', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
        else:
            st.markdown(
                "<p style='color:#9CA3AF;font-size:0.875rem;margin-top:0.5rem'>"
                "Firmenname eingeben oder Ticker aus STOXX 600 wählen.</p>",
                unsafe_allow_html=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — THESIS-ANALYSE  (Russia Exposure × CAR)
# ═════════════════════════════════════════════════════════════════════════════
with tab_thesis:

    st.markdown(
        "<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;"
        "padding:0.85rem 1.1rem;margin-bottom:1.25rem'>"
        "<div style='font-size:0.84rem;font-weight:600;color:#1E40AF'>"
        "Thesis-Analyse — Russia Exposure × Kumulierte Abnormale Renditen</div>"
        "<div style='font-size:0.78rem;color:#1D4ED8;margin-top:3px;line-height:1.5'>"
        "Exposure-Scores aus der Russland-Analyse werden mit CAR[-1,+1], CAR[-3,+3] "
        "und BHAR(30d) verknüpft. Beide Modelle (Mean-Adjusted + Market Model) werden "
        "parallel berechnet."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ── Score-Tabelle ─────────────────────────────────────────────────────────
    divider("Exposure-Scores")
    st.caption(
        "Ticker-Format: SAP.DE · NESN.SW · BP.L · ENI.MI — "
        "Rev/Op Score je 0–3. Scores aus der Russland-Analyse werden automatisch befüllt."
    )

    _df_sc = load_scores()
    _display_cols = ["Ticker", "Unternehmen", "Sektor",
                     "Revenue Score", "Operational Score", "Confidence", "Notizen"]
    _edited = st.data_editor(
        _df_sc[_display_cols] if all(c in _df_sc.columns for c in _display_cols) else _df_sc,
        column_config={
            "Ticker":            st.column_config.TextColumn("Ticker", width="small"),
            "Unternehmen":       st.column_config.TextColumn("Unternehmen", width="medium"),
            "Sektor":            st.column_config.TextColumn("Sektor (GICS)", width="medium"),
            "Revenue Score":     st.column_config.SelectboxColumn(
                "Rev. Score", options=[0, 1, 2, 3], width="small",
                help="0 = <1 % · 1 = 1–5 % · 2 = 5–10 % · 3 = >10 % Russland-Umsatz",
            ),
            "Operational Score": st.column_config.SelectboxColumn(
                "Op. Score", options=[0, 1, 2, 3], width="small",
                help="0 = keine · 1 = begrenzt · 2 = signifikant · 3 = kritisch",
            ),
            "Confidence":        st.column_config.SelectboxColumn(
                "Confidence", options=["High", "Medium", "Low"], width="small",
            ),
            "Notizen":           st.column_config.TextColumn("Notizen / Flags", width="large"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="scores_editor",
        height=min(400, 80 + len(_df_sc) * 36),
    )

    _sc1, _sc2, _sc3 = st.columns([1, 1, 4])
    with _sc1:
        if st.button("Speichern", type="primary", use_container_width=True, key="save_scores"):
            # Merge edited display cols back into full score df
            _full = load_scores()
            for _c in _display_cols:
                if _c in _edited.columns:
                    if len(_edited) == len(_full):
                        _full[_c] = _edited[_c].values
                    else:
                        _full = _edited.copy()
                        break
            save_scores(_full if len(_edited) == len(_full) else _edited)
            st.toast("Scores gespeichert.", icon="✅")
    with _sc2:
        if st.button("Cache leeren", use_container_width=True, key="clear_thesis_cache"):
            calc_ar_thesis.clear()
            st.toast("Cache geleert.")

    # ── Modell-Auswahl ────────────────────────────────────────────────────────
    _valid = _edited.dropna(subset=["Ticker"]).copy()
    _valid = _valid[_valid["Ticker"].str.strip().ne("")]

    if len(_valid) < 2:
        st.info("Mindestens 2 Unternehmen mit Ticker und Scores eintragen.")
        st.stop()

    divider("Modell & Event-Fenster")
    _msel_col, _wsel_col, _ = st.columns([2, 2, 3])
    with _msel_col:
        _model_choice = st.radio(
            "Modell",
            ["Mean-Adjusted", "Market Model (OLS)"],
            horizontal=True,
            label_visibility="visible",
            key="thesis_model",
        )
    with _wsel_col:
        _window_choice = st.radio(
            "Event-Fenster",
            ["CAR[−1,+1]", "CAR[−3,+3]"],
            horizontal=True,
            label_visibility="visible",
            key="thesis_window",
        )

    _is_mm     = ("Market" in _model_choice)
    _win_sfx   = "_mm" if _is_mm else ""
    _car_col   = ("CAR[-1,+1]" if "1" in _window_choice else "CAR[-3,+3]") + _win_sfx
    _t_col     = ("t[-1,+1]"   if "1" in _window_choice else "t[-3,+3]")   + _win_sfx
    _car_label = f"{'CAR[−1,+1]' if '1' in _window_choice else 'CAR[−3,+3]'} ({'Mkt-Model' if _is_mm else 'Mean-Adj'})"

    st.markdown(
        f"<p style='font-size:0.875rem;color:#6B7280'>"
        f"<b>{len(_valid)}</b> Unternehmen · Benchmark: {_BENCHMARK_TICKER} · "
        f"Schätzfenster: 120 Handelstage, endet 11 Tage vor Event · "
        f"Primärmetrik: <b>{_car_label}</b></p>",
        unsafe_allow_html=True,
    )

    if st.button("CAR / BHAR berechnen", type="primary", key="calc_ar_btn"):
        calc_ar_thesis.clear()
        st.session_state["thesis_ar_ready"] = True

    if not st.session_state.get("thesis_ar_ready"):
        st.stop()

    with st.spinner("Lade Preisdaten & berechne CAR …"):
        _tickers_t = tuple(_valid["Ticker"].str.strip().tolist())
        _df_ar = calc_ar_thesis(_tickers_t)

    if _df_ar.empty:
        st.warning("Keine Preisdaten geladen. Ticker prüfen.")
        st.stop()

    # ── Merge ─────────────────────────────────────────────────────────────────
    _valid2 = _valid.set_index("Ticker").copy()
    _valid2.index = _valid2.index.str.strip()
    _df_merged = _valid2.join(_df_ar, how="left")
    _df_merged["Combined Score"] = (
        _df_merged["Revenue Score"].fillna(0).astype(int)
        + _df_merged["Operational Score"].fillna(0).astype(int)
    )

    _df_plot = _df_merged.dropna(subset=[_car_col]) if _car_col in _df_merged.columns else pd.DataFrame()
    _n_ok    = len(_df_plot)
    _n_miss  = len(_df_merged) - _n_ok
    st.caption(
        f"{_n_ok} von {len(_df_merged)} Aktien mit {_car_label} · "
        + (f"{_n_miss} ohne Preisdaten (Ticker prüfen)" if _n_miss else "alle geladen ✓")
    )

    if _df_plot.empty:
        st.warning("Keine verwertbaren Daten. Bitte erst 'CAR / BHAR berechnen' klicken.")
        st.stop()

    # ── Scatter helper ────────────────────────────────────────────────────────
    _SCORE_COLORS = {0: "#9CA3AF", 1: "#2563EB", 2: "#F59E0B", 3: "#DC2626"}
    _SCORE_LABELS = {0: "0 – Keine", 1: "1 – Gering", 2: "2 – Signifikant", 3: "3 – Kritisch"}

    def _make_scatter(df: pd.DataFrame, score_col: str, y_col: str, y_label: str, title: str) -> go.Figure:
        _df_s = df.dropna(subset=[score_col, y_col])
        if _df_s.empty:
            return go.Figure()
        rng    = np.random.default_rng(42)
        jitter = rng.uniform(-0.12, 0.12, len(_df_s))
        x_j    = _df_s[score_col].astype(float) + jitter
        y_pct  = _df_s[y_col] * 100
        pt_colors = [_SCORE_COLORS.get(int(s), "#9CA3AF") for s in _df_s[score_col].fillna(0).astype(int)]

        _t_c = _t_col if y_col == _car_col else None
        hover = []
        for idx, row in _df_s.iterrows():
            _t_val = f"  t={row[_t_c]:.2f}" if (_t_c and _t_c in row and pd.notna(row[_t_c])) else ""
            hover.append(
                f"<b>{idx}</b><br>"
                f"{row.get('Unternehmen', '')}<br>"
                f"{score_col}: {int(row[score_col]) if pd.notna(row[score_col]) else '?'}<br>"
                f"{y_label}: {row[y_col]*100:+.2f}%{_t_val}"
            )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_j, y=y_pct, mode="markers",
            marker=dict(color=pt_colors, size=10, opacity=0.85,
                        line=dict(color="white", width=1.5)),
            text=hover, hoverinfo="text", showlegend=False,
        ))
        if len(_df_s) <= 40:
            fig.add_trace(go.Scatter(
                x=x_j, y=y_pct, mode="text",
                text=_df_s.index.tolist(),
                textposition="top center",
                textfont=dict(size=8, color="#6B7280"),
                hoverinfo="skip", showlegend=False,
            ))

        _xv = _df_s[score_col].astype(float).values
        _yv = y_pct.values
        _m  = ~(np.isnan(_xv) | np.isnan(_yv))
        if _m.sum() >= 4 and len(np.unique(_xv[_m])) >= 2:
            coeffs = np.polyfit(_xv[_m], _yv[_m], 1)
            _xr    = np.linspace(_xv[_m].min(), _xv[_m].max(), 60)
            _yr    = np.polyval(coeffs, _xr)
            ss_res = np.sum((_yv[_m] - np.polyval(coeffs, _xv[_m])) ** 2)
            ss_tot = np.sum((_yv[_m] - _yv[_m].mean()) ** 2)
            r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            corr   = np.corrcoef(_xv[_m], _yv[_m])[0, 1]
            fig.add_trace(go.Scatter(
                x=_xr, y=_yr, mode="lines",
                line=dict(color="#94A3B8", dash="dash", width=1.5),
                name=f"OLS  r={corr:+.3f}  R²={r2:.3f}  β={coeffs[0]:+.2f}  n={_m.sum()}",
                showlegend=True,
            ))

        fig.add_hline(y=0, line_color="#E5E7EB", line_width=1)
        fig.update_layout(
            height=420, margin=dict(l=0, r=0, t=36, b=0),
            title=dict(text=title, font=dict(size=13, color="#374151")),
            xaxis=dict(
                title="Exposure Score", tickvals=[0, 1, 2, 3],
                ticktext=[_SCORE_LABELS[i] for i in range(4)],
                gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(size=10, color="#6B7280"), range=[-0.5, 3.5],
            ),
            yaxis=dict(
                title=f"{y_label} (%)", tickformat=".1f",
                gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(size=11, color="#6B7280"),
            ),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            legend=dict(orientation="h", y=1.06, x=1, xanchor="right",
                        font=dict(size=10, color="#6B7280")),
        )
        return fig

    def _make_group_bar(df: pd.DataFrame, score_col: str, y_col: str, y_label: str, title: str) -> go.Figure:
        _df_g = df.dropna(subset=[score_col, y_col])
        if _df_g.empty:
            return go.Figure()
        grp = (_df_g.groupby(score_col)[y_col]
                .agg(["mean", "sem", "count"]).reset_index())
        grp["mean_pct"] = grp["mean"] * 100
        grp["err_pct"]  = grp["sem"]  * 100 * 1.96
        bar_colors = [_SCORE_COLORS.get(int(s), "#9CA3AF") for s in grp[score_col]]
        fig = go.Figure(go.Bar(
            x=[_SCORE_LABELS.get(int(s), str(s)) for s in grp[score_col]],
            y=grp["mean_pct"],
            error_y=dict(type="data", array=grp["err_pct"].tolist(),
                         color="#9CA3AF", thickness=1.5, width=6),
            marker_color=bar_colors,
            text=[f"{v:+.2f}%\n(n={n})" for v, n in zip(grp["mean_pct"], grp["count"])],
            textposition="outside",
            hovertemplate=f"%{{x}}<br>Ø {y_label}: %{{y:.3f}}%<extra></extra>",
        ))
        fig.add_hline(y=0, line_color="#E5E7EB", line_width=1)
        fig.update_layout(
            height=340, margin=dict(l=0, r=0, t=36, b=0),
            title=dict(text=title, font=dict(size=13, color="#374151")),
            yaxis=dict(tickformat=".1f", gridcolor="#F3F4F6", zeroline=False,
                       title=f"Ø {y_label} (%)", tickfont=dict(size=11, color="#6B7280")),
            xaxis=dict(tickfont=dict(size=10, color="#374151")),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False,
        )
        return fig

    # ── Scatter-Plots: primäres CAR-Fenster ───────────────────────────────────
    divider(f"Scatter: Exposure vs. {_car_label}")
    _pc1, _pc2 = st.columns(2)
    with _pc1:
        st.plotly_chart(
            _make_scatter(_df_plot, "Revenue Score", _car_col, _car_label,
                          f"Revenue Score vs. {_car_label}"),
            use_container_width=True,
        )
    with _pc2:
        st.plotly_chart(
            _make_scatter(_df_plot, "Operational Score", _car_col, _car_label,
                          f"Operational Score vs. {_car_label}"),
            use_container_width=True,
        )

    # ── Robustness: anderes CAR-Fenster ──────────────────────────────────────
    _rob_win    = "CAR[-3,+3]" if "1" in _window_choice else "CAR[-1,+1]"
    _rob_col    = _rob_win + _win_sfx
    _rob_label  = f"{'CAR[−3,+3]' if '1' in _window_choice else 'CAR[−1,+1]'} ({'Mkt-Model' if _is_mm else 'Mean-Adj'}) — Robustness"
    _df_rob     = _df_merged.dropna(subset=[_rob_col]) if _rob_col in _df_merged.columns else pd.DataFrame()
    if not _df_rob.empty:
        divider(f"Robustness: {_rob_label}")
        _rc1, _rc2 = st.columns(2)
        with _rc1:
            st.plotly_chart(
                _make_scatter(_df_rob, "Revenue Score", _rob_col, _rob_label,
                              f"Revenue Score vs. {_rob_label}"),
                use_container_width=True,
            )
        with _rc2:
            st.plotly_chart(
                _make_scatter(_df_rob, "Operational Score", _rob_col, _rob_label,
                              f"Operational Score vs. {_rob_label}"),
                use_container_width=True,
            )

    # ── 30-Tage-BHAR ─────────────────────────────────────────────────────────
    _bhar_col   = "BHAR_30d"
    _df_bhar    = _df_merged.dropna(subset=[_bhar_col]) if _bhar_col in _df_merged.columns else pd.DataFrame()
    if not _df_bhar.empty:
        divider("30-Tage BHAR nach Score-Gruppe")
        _bc1, _bc2 = st.columns(2)
        with _bc1:
            st.plotly_chart(
                _make_group_bar(_df_bhar, "Revenue Score", _bhar_col,
                                "BHAR 30d", "Ø BHAR(30d) nach Revenue Score"),
                use_container_width=True,
            )
        with _bc2:
            st.plotly_chart(
                _make_group_bar(_df_bhar, "Operational Score", _bhar_col,
                                "BHAR 30d", "Ø BHAR(30d) nach Operational Score"),
                use_container_width=True,
            )

    # ── Gruppen-Balken: primäres CAR ──────────────────────────────────────────
    divider(f"Ø {_car_label} nach Score-Gruppe")
    _gc1, _gc2 = st.columns(2)
    with _gc1:
        st.plotly_chart(
            _make_group_bar(_df_plot, "Revenue Score", _car_col, _car_label,
                            f"Ø {_car_label} nach Revenue Score"),
            use_container_width=True,
        )
    with _gc2:
        st.plotly_chart(
            _make_group_bar(_df_plot, "Operational Score", _car_col, _car_label,
                            f"Ø {_car_label} nach Operational Score"),
            use_container_width=True,
        )

    # ── Deskriptive Statistik ─────────────────────────────────────────────────
    divider("Deskriptive Statistik nach Gruppe")
    _stat_rows = []
    for _sc_col in ["Revenue Score", "Operational Score"]:
        for _sc_val, _grp in _df_plot.groupby(_sc_col):
            _row = {
                "Dimension": _sc_col, "Score": int(_sc_val), "n": len(_grp),
            }
            for _mc, _ml in [(_car_col, _car_label), (_rob_col, _rob_label), (_bhar_col, "BHAR_30d")]:
                if _mc in _grp.columns:
                    _v = _grp[_mc].dropna()
                    _row[f"Ø {_ml[:14]}"] = _v.mean() if len(_v) else np.nan
                    _row[f"Std {_ml[:14]}"] = _v.std() if len(_v) else np.nan
            _stat_rows.append(_row)
    if _stat_rows:
        _df_stat = pd.DataFrame(_stat_rows)
        _num_cols_stat = [c for c in _df_stat.columns if c not in ("Dimension", "Score", "n")]
        st.dataframe(
            _df_stat.style.format({c: "{:+.4f}" for c in _num_cols_stat}, na_rep="—"),
            use_container_width=True, hide_index=True,
            height=58 + len(_df_stat) * 35,
        )

    # ── Rohdaten ──────────────────────────────────────────────────────────────
    divider("Rohdaten")
    _car_display_cols = [c for c in [
        "CAR[-1,+1]", "t[-1,+1]", "CAR[-3,+3]", "t[-3,+3]",
        "CAR[-1,+1]_mm", "t[-1,+1]_mm", "CAR[-3,+3]_mm", "t[-3,+3]_mm",
        "BHAR_30d", "CR_30d", "AR", "Z-Score", "Return 24.02.",
        "alpha", "beta",
    ] if c in _df_merged.columns]
    _base_cols = [c for c in ["Unternehmen", "Sektor", "Revenue Score", "Operational Score",
                               "Combined Score", "Confidence", "Notizen"]
                  if c in _df_merged.columns]
    _show_cols = _base_cols + _car_display_cols
    _df_raw_disp = _df_merged[_show_cols].sort_values(_car_col if _car_col in _df_merged.columns else _show_cols[0])
    _fmt_raw = {c: "{:+.4f}" for c in _car_display_cols if c not in ("alpha", "beta")}
    _fmt_raw.update({"alpha": "{:+.5f}", "beta": "{:.4f}"})
    _grad_raw = [c for c in [_car_col, "AR"] if c in _df_raw_disp.columns]
    st.dataframe(
        _df_raw_disp.style
            .format(_fmt_raw, na_rep="—")
            .background_gradient(subset=_grad_raw, cmap="RdYlGn", vmin=-0.08, vmax=0.08),
        use_container_width=True,
        height=min(600, 58 + len(_df_raw_disp) * 35),
    )

    # ── Excel-Export ──────────────────────────────────────────────────────────
    divider("Excel-Export")
    _thesis_buf = io.BytesIO()
    with pd.ExcelWriter(_thesis_buf, engine="openpyxl") as _xw:
        # Sheet 1: Rohdaten (all metrics)
        _df_merged.reset_index().to_excel(_xw, sheet_name="Rohdaten", index=False)
        # Sheet 2: Deskriptive Statistik
        if _stat_rows:
            _df_stat.to_excel(_xw, sheet_name="Deskriptive Statistik", index=False)
        # Sheet 3+4: Gruppen pro Score-Typ
        for _sc_col, _sh in [("Revenue Score", "Gruppe Rev"), ("Operational Score", "Gruppe Op")]:
            if _car_col in _df_plot.columns:
                _gdf = (
                    _df_plot.dropna(subset=[_sc_col, _car_col])
                    .groupby(_sc_col)[_car_col]
                    .agg(["mean", "std", "sem", "count", "min", "max"])
                    .reset_index()
                )
                _gdf.to_excel(_xw, sheet_name=_sh, index=False)
        # Sheet 5: Scores + Justifications (audit trail)
        _full_sc = load_scores()
        if not _full_sc.empty:
            _full_sc.to_excel(_xw, sheet_name="Scores & Audit", index=False)

    _today_th = date.today()
    excel_export_card(
        _thesis_buf,
        f"thesis_analyse_{_today_th}.xlsx",
        len(_df_merged),
        _today_th, _today_th,
        "Rohdaten · Deskriptive Statistik · Gruppen Rev/Op · Scores & Audit Trail",
    )
