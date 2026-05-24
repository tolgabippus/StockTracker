"""
app.py — Globaler Marktvergleich & Einzelaktien

Start:
    streamlit run app.py
"""

import importlib
import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

import data.constituents as _constituents_mod
from data.constituents import STOXX50_TICKERS

ROOT       = Path(__file__).resolve().parent
_FULL_JSON = ROOT / "data" / "stoxx600_full_tickers.json"


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

/* Sidebar collapse button */
[data-testid="collapsedControl"] {
    background-color: #F8FAFC !important;
    border-right: 1px solid #E2E8F0 !important;
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
                        padding:1rem 1.25rem;margin:0.75rem 0 0.5rem 0;
                        display:flex;align-items:center;gap:1rem">
              <div style="font-size:1.75rem;line-height:1;flex-shrink:0">&#128190;</div>
              <div style="flex:1;min-width:0">
                <div style="font-size:0.84rem;font-weight:600;color:#111827;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{fname}</div>
                <div style="font-size:0.75rem;color:#6B7280;margin-top:3px">
                  {n_items} Einträge &middot;
                  {start.strftime('%d.%m.%Y')} &ndash; {end.strftime('%d.%m.%Y')} &middot;
                  {_kb} KB &middot; {sheet_desc}
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

    st.subheader("Zeitraum")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Von", value=date(2021, 1, 1), label_visibility="visible")
    with c2:
        end_date = st.date_input("Bis", value=date.today(), label_visibility="visible")

    st.subheader("Darstellung")
    mode = st.radio("Modus", ["Normiert (Basis 100)", "Absolut"],
                    horizontal=True, label_visibility="collapsed")
    show_event = st.checkbox("Kriegsbeginn markieren", value=True)

    st.markdown("<div style='height:1px;background:#E2E8F0;margin-top:2rem;margin-bottom:0.5rem'></div>",
                unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.72rem;color:#C4C9D4'>Kursdaten: Yahoo Finance</div>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='margin-bottom:2px'>Globaler Marktvergleich</h1>"
    f"<p style='font-size:0.84rem;color:#9CA3AF;margin:0 0 1rem 0'>"
    f"{start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;{mode}</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_markt, tab_aktien = st.tabs(["Marktvergleich", "Einzelaktien"])


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
            st.markdown(
                f"<p style='font-size:0.68rem;font-weight:700;color:#9CA3AF;"
                f"text-transform:uppercase;letter-spacing:0.08em;"
                f"margin:0 0 0.4rem 0;border-bottom:1px solid #F1F5F9;padding-bottom:0.3rem'>"
                f"{region}</p>",
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
        if st.button(f"{section_label} laden", type="primary"):
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
