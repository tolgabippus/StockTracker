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

ROOT         = Path(__file__).resolve().parent
_FULL_JSON   = ROOT / "data" / "stoxx600_full_tickers.json"
_SCORES_PATH = ROOT / "data" / "russia_scores.json"


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
EVENT_DATE = pd.Timestamp("2022-02-24")
EVENT_STR  = "2022-02-24"


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
    _empty = pd.DataFrame({
        "Ticker":             pd.Series(dtype=str),
        "Unternehmen":        pd.Series(dtype=str),
        "Sektor":             pd.Series(dtype=str),
        "Revenue Score":      pd.Series(dtype=int),
        "Operational Score":  pd.Series(dtype=int),
        "Confidence":         pd.Series(dtype=str),
        "Notizen":            pd.Series(dtype=str),
    })
    if not _SCORES_PATH.exists():
        return _empty
    try:
        records = json.loads(_SCORES_PATH.read_text())
        df = pd.DataFrame(records)
        for col in ["Revenue Score", "Operational Score"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        return df
    except Exception:
        return _empty


def save_scores(df: pd.DataFrame) -> None:
    """Persist Russia exposure scores to JSON file."""
    _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCORES_PATH.write_text(
        json.dumps(df.to_dict(orient="records"), indent=2, ensure_ascii=False)
    )


@st.cache_data(show_spinner=False, ttl=3600)
def calc_ar_thesis(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Download prices and compute ARs for the event date (fixed window 2020–2022)."""
    raw = download_batch(tickers, "2020-01-01", "2022-04-01")
    if raw.empty:
        return pd.DataFrame()
    rows = []
    for ticker in tickers:
        if ticker not in raw.columns:
            continue
        col = raw[ticker].dropna()
        if len(col) < 20:
            continue
        r = np.log(col / col.shift(1)).dropna()
        ev = r.index[(r.index >= EVENT_DATE) & (r.index <= EVENT_DATE + pd.Timedelta(days=4))]
        r_event = float(r.loc[ev[0]]) if len(ev) else np.nan
        pre   = r[r.index < EVENT_DATE].tail(60)
        r_mu  = pre.mean()     if len(pre) > 10 else np.nan
        r_sig = pre.std(ddof=1) if len(pre) > 10 else np.nan
        ar = (r_event - r_mu) if not (np.isnan(r_event) or np.isnan(r_mu)) else np.nan
        z  = (ar / r_sig)     if (r_sig and r_sig > 0 and not np.isnan(ar)) else np.nan
        rows.append({"Ticker": ticker, "AR": ar, "Z-Score": z, "Return 24.02.": r_event})
    return pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()


def parse_russia_scores(text: str) -> dict:
    """Extract scores from AI response — machine-readable block first, table as fallback."""
    rev  = re.search(r'REVENUE_SCORE:\s*([0-3])', text)
    ops  = re.search(r'OPERATIONAL_SCORE:\s*([0-3])', text)
    conf = re.search(r'CONFIDENCE:\s*(High|Medium|Low)', text, re.IGNORECASE)
    # Fallback: parse from markdown table / inline text
    if not rev:
        rev  = re.search(r'Revenue Exposure Score[^\d]*([0-3])', text)
    if not ops:
        ops  = re.search(r'Operational Exposure Score[^\d]*([0-3])', text)
    return {
        "revenue_score":      int(rev.group(1))           if rev  else None,
        "operational_score":  int(ops.group(1))           if ops  else None,
        "confidence":         conf.group(1).capitalize()  if conf else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Russland-Analyse — Systemprompt & API-Wrapper
# ─────────────────────────────────────────────────────────────────────────────
_RUSSIA_SYS = """\
You are an academic research assistant supporting a bachelor thesis on the stock market effects of EU and US sanctions against Russia in 2022 on European large-cap firms in the STOXX Europe 600.

Your task is to assess each company's Russian market exposure before the Russian full-scale invasion on 24 February 2022.

For each company, collect and evaluate information on Russian exposure from reliable sources such as annual reports, company filings, investor presentations, official company statements, press releases, reputable financial databases, and credible news sources.

Focus on two main exposure dimensions:

1. Revenue Exposure
Assess the extent to which the company generated sales or revenue in Russia before 24 February 2022.

Assign a Revenue Exposure Score:
0 = No identifiable Russian revenue exposure or exposure below 1% of total revenue.
1 = Low exposure: Russia-related revenue approximately 1–5% of total revenue.
2 = Moderate exposure: Russia-related revenue approximately 5–10% of total revenue.
3 = High exposure: Russia-related revenue above 10% of total revenue.

If exact revenue shares are unavailable, estimate the score based on qualitative evidence, but clearly flag the estimate.

2. Operational Exposure
Assess the extent to which the company had operational, physical, or strategic business exposure to Russia before 24 February 2022.

Include the following subdimensions when evaluating Operational Exposure:
- Russian subsidiaries
- production facilities
- retail stores or distribution networks
- local employees
- joint ventures
- physical assets
- supply-chain dependence
- strategic importance of Russia for the company's business model

Assign an Operational Exposure Score:
0 = No identifiable operational presence in Russia.
1 = Limited operational exposure, such as sales offices, small subsidiaries, minor distribution activities, or limited local staff.
2 = Significant operational exposure, such as multiple subsidiaries, relevant local operations, meaningful employee presence, important distribution networks, or notable assets.
3 = Critical operational exposure, such as major production facilities, substantial local assets, large-scale employee presence, strategically important joint ventures, or strong dependence on Russian supply chains or inputs.

Important: Do not create separate final scores for Asset Exposure, Supply Chain Exposure, or Strategic Importance. Instead, use these as subdimensions when assigning the Operational Exposure Score.

Rules:
- Base the assessment on information available before or shortly after 24 February 2022.
- Avoid using later divestment outcomes as direct evidence of pre-invasion exposure unless they reveal information about pre-existing Russian operations.
- Clearly distinguish between factual evidence and inference.
- If no reliable information is found, assign 0 only if there is evidence of no exposure. Otherwise write "Unknown" and explain why.
- Do not overstate exposure based on vague mentions of Eastern Europe, CIS, or emerging markets unless Russia is specifically identified.
- Prefer conservative scoring when evidence is ambiguous.
- Include short justifications for every score.
- Use consistent scoring across all firms.

Output Format:
Produce the assessment as a Markdown table with the following columns, then add an explanation section below the table.

| Field | Content |
|---|---|
| Company Name | Full legal name |
| Ticker | Stock ticker (e.g. SIE.DE) |
| Country | Country of headquarters |
| Sector | GICS sector |
| Revenue Exposure Score | 0 / 1 / 2 / 3 |
| Revenue Exposure Evidence | Short justification with source citation |
| Operational Exposure Score | 0 / 1 / 2 / 3 |
| Operational Exposure Evidence | Short justification with source citation |
| Confidence Level | High / Medium / Low |
| Sources | List of sources used |
| Notes | Flags, caveats, or inferences clearly marked as [ESTIMATE] or [INFERRED] |

After the table, add a brief paragraph explaining how the scores were assigned and any limitations in the data.

Confidence Level definitions:
- High = based on quantitative disclosures or multiple reliable sources.
- Medium = based on credible qualitative evidence but limited quantitative detail.
- Low = based on indirect evidence, estimates, or incomplete information.

IMPORTANT: At the very end of your response, always append this exact block (required for automated processing — never skip or modify the format):

```scores
REVENUE_SCORE: [0|1|2|3]
OPERATIONAL_SCORE: [0|1|2|3]
CONFIDENCE: [High|Medium|Low]
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
tab_markt, tab_aktien, tab_russia, tab_thesis = st.tabs(
    ["Indizes", "Einzelaktien", "Russland-Analyse", "Thesis-Analyse"]
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
# TAB 3 — RUSSLAND-ANALYSE
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
        _ticker_for_ar = ""
        _inp_col, _ = st.columns([3, 2])
        with _inp_col:
            if _inp_mode == "Firmenname eingeben":
                _company_name = st.text_input(
                    "Firmenname",
                    placeholder="z.B. Renault, Volkswagen AG, BASF SE",
                    label_visibility="collapsed",
                    key="russia_company_text",
                )
                _ticker_for_ar = st.text_input(
                    "Ticker",
                    placeholder="Ticker für AR-Berechnung, z.B. RNO.PA · VOW.DE · BAS.DE",
                    label_visibility="collapsed",
                    key="russia_ticker_text",
                ).strip()
            else:
                _ticker_sel = st.selectbox(
                    "STOXX 600 Ticker",
                    options=["— bitte wählen —"] + sorted(STOXX600_TICKERS),
                    label_visibility="collapsed",
                    key="russia_ticker_sel",
                )
                if _ticker_sel != "— bitte wählen —":
                    _company_name = _ticker_sel
                    _ticker_for_ar = _ticker_sel

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
                _result      = st.session_state["russia_cache"][_cache_key]
                _parsed      = parse_russia_scores(_result)
                _rev_sc      = _parsed.get("revenue_score")
                _ops_sc      = _parsed.get("operational_score")
                _conf        = _parsed.get("confidence") or ""
                _eff_ticker  = _ticker_for_ar or (
                    _company_name if _inp_mode != "Firmenname eingeben" else ""
                )

                # ── AR berechnen ─────────────────────────────────────────
                _ar_val = _z_val = None
                if _eff_ticker:
                    with st.spinner("Berechne Abnormale Rendite …"):
                        _ar_df = calc_ar_thesis((_eff_ticker.strip(),))
                    if not _ar_df.empty and _eff_ticker.strip() in _ar_df.index:
                        _ar_val = float(_ar_df.loc[_eff_ticker.strip(), "AR"])
                        _z_val  = float(_ar_df.loc[_eff_ticker.strip(), "Z-Score"])

                # ── Ergebnis-Karte ────────────────────────────────────────
                _SC_COLOR = {0: "#9CA3AF", 1: "#3B82F6", 2: "#F59E0B", 3: "#DC2626"}
                _SC_DESC  = {0: "Keine  <1 %", 1: "Gering  1–5 %",
                             2: "Moderat  5–10 %", 3: "Hoch  >10 %"}
                _OP_DESC  = {0: "Keine", 1: "Begrenzt",
                             2: "Signifikant", 3: "Kritisch"}

                def _kpi(label, val, sub, color):
                    return (
                        f"<div style='text-align:center;padding:0.6rem 0.25rem'>"
                        f"<div style='font-size:0.6rem;font-weight:700;color:#9CA3AF;"
                        f"text-transform:uppercase;letter-spacing:0.07em;"
                        f"margin-bottom:5px'>{label}</div>"
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
                if _ar_val is not None:
                    _ar_clr  = "#16A34A" if _ar_val >= 0 else "#DC2626"
                    _z_sig   = ("Extrem" if abs(_z_val) > 3
                                else "Signifikant" if abs(_z_val) > 2 else "Normal")
                    _cells  += _kpi("AR  24.02.2022", f"{_ar_val*100:+.1f}%",
                                    _eff_ticker, _ar_clr)
                    _cells  += _kpi("Z-Score", f"{_z_val:.2f}", _z_sig, _ar_clr)
                if _conf:
                    _cells += _kpi("Confidence", _conf, "", "#6B7280")

                if _cells:
                    st.markdown(
                        f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
                        f"border-radius:12px;padding:0.75rem 1rem;margin:0.75rem 0;"
                        f"display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr))'>"
                        f"{_cells}</div>",
                        unsafe_allow_html=True,
                    )

                # ── Zur Thesis hinzufügen ─────────────────────────────────
                if _rev_sc is not None:
                    _thesis_label = (
                        f"Zur Thesis-Analyse hinzufügen"
                        + (" · bereits vorhanden" if (
                            _eff_ticker and _eff_ticker in
                            load_scores()["Ticker"].values
                        ) else "")
                    )
                    if st.button(_thesis_label, type="primary",
                                 use_container_width=False, key="add_thesis"):
                        _df_ex = load_scores()
                        _tk    = _eff_ticker or _company_name
                        _new   = {
                            "Ticker":            _tk,
                            "Unternehmen":       _company_name
                                                 if _inp_mode == "Firmenname eingeben"
                                                 else "",
                            "Sektor":            "",
                            "Revenue Score":     _rev_sc,
                            "Operational Score": _ops_sc or 0,
                            "Confidence":        _conf,
                            "Notizen":           "",
                        }
                        _mask = _df_ex["Ticker"] == _tk
                        if _mask.any():
                            for _k, _v in _new.items():
                                _df_ex.loc[_mask, _k] = _v
                        else:
                            _df_ex = pd.concat(
                                [_df_ex, pd.DataFrame([_new])], ignore_index=True
                            )
                        save_scores(_df_ex)
                        st.toast(f"{_tk} gespeichert — jetzt im Thesis-Analyse Tab.", icon="✅")

                # ── Vollständige Analyse ──────────────────────────────────
                divider(f"Vollständige Analyse: {_company_name}")
                # Hide the machine-readable scores block from display
                _display_result = re.sub(
                    r'```scores\n.*?```', '', _result, flags=re.DOTALL
                ).strip()
                st.markdown(_display_result)
                divider()
                _dl_col, _ = st.columns([2, 3])
                with _dl_col:
                    st.download_button(
                        label="Analyse herunterladen (.md)",
                        data=_result.encode("utf-8"),
                        file_name=(
                            f"russland_analyse_"
                            f"{_company_name.replace(' ', '_').replace('/', '_')}.md"
                        ),
                        mime="text/markdown",
                        use_container_width=True,
                    )
        else:
            st.markdown(
                "<p style='color:#9CA3AF;font-size:0.875rem;margin-top:0.5rem'>"
                "Firmenname + Ticker eingeben oder Ticker aus STOXX 600 wählen.</p>",
                unsafe_allow_html=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — THESIS-ANALYSE  (Russia Exposure × Abnormale Renditen)
# ═════════════════════════════════════════════════════════════════════════════
with tab_thesis:

    st.markdown(
        "<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;"
        "padding:0.85rem 1.1rem;margin-bottom:1.25rem'>"
        "<div style='font-size:0.84rem;font-weight:600;color:#1E40AF'>"
        "Thesis-Analyse — Russia Exposure × Abnormale Renditen</div>"
        "<div style='font-size:0.78rem;color:#1D4ED8;margin-top:3px;line-height:1.5'>"
        "Trage die Exposure-Scores aus der Russland-Analyse ein, dann berechne die "
        "Abnormalen Renditen vom 24.02.2022. Das Ergebnis ist die Datenbasis für "
        "deine Regressionsanalyse."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ── Score-Tabelle ─────────────────────────────────────────────────────────
    divider("Exposure-Scores")
    st.caption(
        "Ticker-Format: SAP.DE · NESN.SW · BP.L · ENI.MI usw. — "
        "Revenue/Operational Score je 0–3 gemäß Thesis-Methodologie."
    )

    _df_sc = load_scores()
    _edited = st.data_editor(
        _df_sc,
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker", width="small", help="yfinance-Ticker, z.B. SAP.DE"
            ),
            "Unternehmen": st.column_config.TextColumn("Unternehmen", width="medium"),
            "Sektor": st.column_config.TextColumn("Sektor (GICS)", width="medium"),
            "Revenue Score": st.column_config.SelectboxColumn(
                "Rev. Score", options=[0, 1, 2, 3], width="small",
                help="0 = <1 % · 1 = 1–5 % · 2 = 5–10 % · 3 = >10 % Russland-Umsatz",
            ),
            "Operational Score": st.column_config.SelectboxColumn(
                "Op. Score", options=[0, 1, 2, 3], width="small",
                help="0 = keine · 1 = begrenzt · 2 = signifikant · 3 = kritisch",
            ),
            "Confidence": st.column_config.SelectboxColumn(
                "Confidence", options=["High", "Medium", "Low"], width="small",
            ),
            "Notizen": st.column_config.TextColumn("Notizen / Flags", width="large"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="scores_editor",
        height=min(380, 80 + len(_df_sc) * 36),
    )

    _sc1, _sc2, _sc3 = st.columns([1, 1, 4])
    with _sc1:
        if st.button("Speichern", type="primary", use_container_width=True, key="save_scores"):
            save_scores(_edited)
            st.toast("Scores gespeichert.", icon="✅")
    with _sc2:
        if st.button("Cache leeren", use_container_width=True, key="clear_thesis_cache"):
            calc_ar_thesis.clear()
            st.toast("Cache geleert.")

    # ── AR berechnen ──────────────────────────────────────────────────────────
    _valid = _edited.dropna(subset=["Ticker"]).copy()
    _valid = _valid[_valid["Ticker"].str.strip().ne("")]

    if len(_valid) < 2:
        st.info("Mindestens 2 Unternehmen mit Ticker und Scores eintragen.")
        st.stop()

    divider("Abnormale Renditen")
    st.markdown(
        f"<p style='font-size:0.875rem;color:#6B7280'>"
        f"<b>{len(_valid)}</b> Unternehmen · "
        f"Schätzfenster: 60 Handelstage vor 24.02.2022 · "
        f"AR = Return(24.02.) − Ø(Schätzfenster)</p>",
        unsafe_allow_html=True,
    )

    if st.button("Abnormale Renditen berechnen", type="primary", key="calc_ar_btn"):
        st.session_state["thesis_ar_ready"] = True

    if not st.session_state.get("thesis_ar_ready"):
        st.stop()

    with st.spinner("Lade Preisdaten …"):
        _tickers_t = tuple(_valid["Ticker"].str.strip().tolist())
        _df_ar = calc_ar_thesis(_tickers_t)

    if _df_ar.empty:
        st.warning("Keine Preisdaten geladen. Ticker prüfen.")
        st.stop()

    # ── Merge ─────────────────────────────────────────────────────────────────
    _valid = _valid.set_index("Ticker")
    _valid.index = _valid.index.str.strip()
    _df_merged = _valid.join(_df_ar, how="left")
    _df_merged["Combined Score"] = (
        _df_merged["Revenue Score"].fillna(0).astype(int)
        + _df_merged["Operational Score"].fillna(0).astype(int)
    )
    _df_plot = _df_merged.dropna(subset=["AR"])
    _n_ok   = len(_df_plot)
    _n_miss = len(_df_merged) - _n_ok
    st.caption(
        f"{_n_ok} von {len(_df_merged)} Aktien mit AR · "
        + (f"{_n_miss} ohne Preisdaten (Ticker prüfen)" if _n_miss else "alle geladen ✓")
    )

    # ── Scatter helper ────────────────────────────────────────────────────────
    _SCORE_COLORS = {0: "#9CA3AF", 1: "#2563EB", 2: "#F59E0B", 3: "#DC2626"}
    _SCORE_LABELS = {0: "0 – Keine", 1: "1 – Gering", 2: "2 – Signifikant", 3: "3 – Kritisch"}

    def _make_scatter(df: pd.DataFrame, score_col: str, title: str) -> go.Figure:
        rng    = np.random.default_rng(42)
        jitter = rng.uniform(-0.12, 0.12, len(df))
        x_j    = df[score_col].astype(float) + jitter
        y_pct  = df["AR"] * 100

        pt_colors = [_SCORE_COLORS.get(int(s), "#9CA3AF")
                     for s in df[score_col].fillna(0).astype(int)]
        hover = [
            f"<b>{idx}</b><br>"
            f"{row.get('Unternehmen', '')}<br>"
            f"{score_col}: {int(row[score_col]) if pd.notna(row[score_col]) else '?'}<br>"
            f"AR: {row['AR']*100:+.2f}%<br>"
            f"Z: {row['Z-Score']:.2f}" if pd.notna(row.get("Z-Score")) else
            f"<b>{idx}</b><br>AR: {row['AR']*100:+.2f}%"
            for idx, row in df.iterrows()
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_j, y=y_pct, mode="markers",
            marker=dict(color=pt_colors, size=10, opacity=0.85,
                        line=dict(color="white", width=1.5)),
            text=hover, hoverinfo="text", showlegend=False,
        ))
        if len(df) <= 30:
            fig.add_trace(go.Scatter(
                x=x_j, y=y_pct, mode="text",
                text=df.index.tolist(),
                textposition="top center",
                textfont=dict(size=8, color="#6B7280"),
                hoverinfo="skip", showlegend=False,
            ))

        # OLS trend line + R²
        _xv = df[score_col].astype(float).values
        _yv = y_pct.values
        _m  = ~(np.isnan(_xv) | np.isnan(_yv))
        if _m.sum() >= 4 and len(np.unique(_xv[_m])) >= 2:
            coeffs  = np.polyfit(_xv[_m], _yv[_m], 1)
            _xr     = np.linspace(_xv[_m].min(), _xv[_m].max(), 60)
            _yr     = np.polyval(coeffs, _xr)
            ss_res  = np.sum((_yv[_m] - np.polyval(coeffs, _xv[_m])) ** 2)
            ss_tot  = np.sum((_yv[_m] - _yv[_m].mean()) ** 2)
            r2      = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            slope   = coeffs[0]
            fig.add_trace(go.Scatter(
                x=_xr, y=_yr, mode="lines",
                line=dict(color="#94A3B8", dash="dash", width=1.5),
                name=f"OLS  R²={r2:.3f}  β={slope:+.2f}",
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
                tickfont=dict(size=10, color="#6B7280"),
                range=[-0.5, 3.5],
            ),
            yaxis=dict(
                title="Abnormale Rendite (%)", tickformat=".1f",
                gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(size=11, color="#6B7280"),
            ),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            legend=dict(orientation="h", y=1.06, x=1, xanchor="right",
                        font=dict(size=10, color="#6B7280")),
        )
        return fig

    # ── Gruppen-Balken helper ─────────────────────────────────────────────────
    def _make_group_bar(df: pd.DataFrame, score_col: str, title: str) -> go.Figure:
        grp = (df.groupby(score_col)["AR"]
                 .agg(["mean", "sem", "count"])
                 .reset_index())
        grp["mean_pct"] = grp["mean"] * 100
        grp["err_pct"]  = grp["sem"]  * 100 * 1.96
        bar_colors = [_SCORE_COLORS.get(int(s), "#9CA3AF") for s in grp[score_col]]
        fig = go.Figure(go.Bar(
            x=[_SCORE_LABELS.get(int(s), str(s)) for s in grp[score_col]],
            y=grp["mean_pct"],
            error_y=dict(type="data", array=grp["err_pct"].tolist(),
                         color="#9CA3AF", thickness=1.5, width=6),
            marker_color=bar_colors,
            text=[f"{v:+.2f}%<br>(n={n})" for v, n in zip(grp["mean_pct"], grp["count"])],
            textposition="outside",
            hovertemplate="%{x}<br>Ø AR: %{y:.3f}%<extra></extra>",
        ))
        fig.add_hline(y=0, line_color="#E5E7EB", line_width=1)
        fig.update_layout(
            height=340, margin=dict(l=0, r=0, t=36, b=0),
            title=dict(text=title, font=dict(size=13, color="#374151")),
            yaxis=dict(tickformat=".1f", gridcolor="#F3F4F6", zeroline=False,
                       title="Ø Abnormale Rendite (%)", tickfont=dict(size=11, color="#6B7280")),
            xaxis=dict(tickfont=dict(size=10, color="#374151")),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False,
        )
        return fig

    # ── Plots ─────────────────────────────────────────────────────────────────
    divider("Revenue Exposure vs. AR")
    _pc1, _pc2 = st.columns(2)
    with _pc1:
        st.plotly_chart(
            _make_scatter(_df_plot, "Revenue Score",
                          "Revenue Score vs. Abnormale Rendite (24.02.2022)"),
            use_container_width=True,
        )
    with _pc2:
        st.plotly_chart(
            _make_scatter(_df_plot, "Operational Score",
                          "Operational Score vs. Abnormale Rendite (24.02.2022)"),
            use_container_width=True,
        )

    divider("Durchschnittliche AR nach Score-Gruppe")
    _gc1, _gc2 = st.columns(2)
    with _gc1:
        st.plotly_chart(
            _make_group_bar(_df_plot, "Revenue Score", "Ø AR nach Revenue Score"),
            use_container_width=True,
        )
    with _gc2:
        st.plotly_chart(
            _make_group_bar(_df_plot, "Operational Score", "Ø AR nach Operational Score"),
            use_container_width=True,
        )

    # ── Statistik-Tabelle ─────────────────────────────────────────────────────
    divider("Deskriptive Statistik nach Gruppe")
    _stat_rows = []
    for _sc_col in ["Revenue Score", "Operational Score"]:
        for _sc_val, _grp in _df_plot.groupby(_sc_col):
            _stat_rows.append({
                "Dimension":   _sc_col,
                "Score":       int(_sc_val),
                "n":           len(_grp),
                "Ø AR":        _grp["AR"].mean(),
                "Median AR":   _grp["AR"].median(),
                "Std AR":      _grp["AR"].std(),
                "Min AR":      _grp["AR"].min(),
                "Max AR":      _grp["AR"].max(),
            })
    if _stat_rows:
        _df_stat = pd.DataFrame(_stat_rows)
        _fmt_stat = {c: "{:+.4f}" for c in ["Ø AR", "Median AR", "Std AR", "Min AR", "Max AR"]}
        st.dataframe(
            _df_stat.style.format(_fmt_stat),
            use_container_width=True, hide_index=True,
            height=58 + len(_df_stat) * 35,
        )

    # ── Rohdaten-Tabelle ──────────────────────────────────────────────────────
    divider("Rohdaten")
    _show_cols = [c for c in [
        "Unternehmen", "Sektor", "Revenue Score", "Operational Score",
        "Combined Score", "Confidence", "AR", "Z-Score", "Return 24.02.", "Notizen",
    ] if c in _df_merged.columns]
    _df_raw_disp = _df_merged[_show_cols].sort_values("AR")
    _fmt_raw = {"AR": "{:+.4f}", "Z-Score": "{:.2f}", "Return 24.02.": "{:+.4f}"}
    _grad_raw = [c for c in ["AR", "Z-Score"] if c in _df_raw_disp.columns]
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
        _df_merged.reset_index().rename(columns={"index": "Ticker"}).to_excel(
            _xw, sheet_name="Rohdaten", index=False
        )
        if _stat_rows:
            _df_stat.to_excel(_xw, sheet_name="Deskriptive Statistik", index=False)
        for _sc_col in ["Revenue Score", "Operational Score"]:
            _gdf = (
                _df_plot.groupby(_sc_col)["AR"]
                .agg(["mean", "std", "sem", "count", "min", "max"])
                .reset_index()
            )
            _gdf.to_excel(
                _xw,
                sheet_name=f"Gruppe {'Rev' if 'Rev' in _sc_col else 'Op'}",
                index=False,
            )

    _today_th = date.today()
    excel_export_card(
        _thesis_buf,
        f"thesis_analyse_{_today_th}.xlsx",
        len(_df_merged),
        _today_th, _today_th,
        "Rohdaten · Deskriptive Statistik · Gruppen Revenue · Gruppen Operational",
    )
