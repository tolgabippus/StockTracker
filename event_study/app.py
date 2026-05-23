"""
app.py — Globaler Marktvergleich

Start:
    streamlit run app.py
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Marktvergleich",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Index-Definitionen
# ---------------------------------------------------------------------------
INDICES: dict[str, dict] = {
    # ── Europa ───────────────────────────────────────────────────────────────
    "Euro STOXX 50": {
        "ticker": "^STOXX50E",
        "region": "Europa",
        "note": "Index direkt",
        "color": "#003F88",
    },
    "STOXX Europe 600": {
        "ticker": "EXSA.DE",
        "region": "Europa",
        "note": "ETF-Proxy: iShares STOXX Europe 600 UCITS ETF",
        "color": "#005BBB",
    },
    "MSCI EM Eastern Europe ex Russia": {
        "ticker": "CE9.DE",
        "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Eastern Europe Capped (Russland seit Feb 2022 ausgeschlossen)",
        "color": "#1A8FE3",
    },
    "STOXX Eastern Europe Large 100": {
        "ticker": "EPOL",
        "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Poland ETF (größter EM-Eastern-Europe-Markt)",
        "color": "#56C5FF",
    },
    "MSCI Europe Small Cap": {
        "ticker": "IEUS",
        "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Europe Small-Cap ETF",
        "color": "#A8DAFF",
    },
    # ── Amerika ──────────────────────────────────────────────────────────────
    "Dow Jones Industrial": {
        "ticker": "^DJI",
        "region": "Amerika",
        "note": "Index direkt",
        "color": "#CC0000",
    },
    "NASDAQ Composite": {
        "ticker": "^IXIC",
        "region": "Amerika",
        "note": "Index direkt",
        "color": "#FF6B35",
    },
    # ── Asien ────────────────────────────────────────────────────────────────
    "S&P Asia 50": {
        "ticker": "AIA",
        "region": "Asien",
        "note": "ETF-Proxy: iShares S&P Asia 50 ETF",
        "color": "#007A33",
    },
    "MSCI AC Asia": {
        "ticker": "AAXJ",
        "region": "Asien",
        "note": "ETF-Proxy: iShares MSCI All Country Asia ex Japan ETF",
        "color": "#00C04B",
    },
    # ── Australien ───────────────────────────────────────────────────────────
    "MSCI Australia Large Cap": {
        "ticker": "EWA",
        "region": "Australien",
        "note": "ETF-Proxy: iShares MSCI Australia ETF",
        "color": "#E6AC00",
    },
}

REGIONS = sorted({v["region"] for v in INDICES.values()})

REGION_ICONS = {
    "Europa":     "🇪🇺",
    "Amerika":    "🇺🇸",
    "Asien":      "🌏",
    "Australien": "🇦🇺",
}

EVENT_DATE     = pd.Timestamp("2022-02-24")
EVENT_DATE_STR = "2022-02-24"   # plotly add_vline braucht einen String


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def download_prices(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    """Download Adj Close prices for all tickers; skips failures silently."""
    frames: list[pd.Series] = []

    for ticker in tickers:
        try:
            raw = yf.download(ticker, start=start, end=end,
                              auto_adjust=True, progress=False)
            if raw.empty:
                continue

            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"].iloc[:, 0]
            else:
                close = raw["Close"]

            close.name = ticker
            frames.append(close)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, axis=1, sort=True).ffill()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize each column to 100 at the first non-NaN value."""
    first = df.apply(lambda col: col.dropna().iloc[0] if col.dropna().size else np.nan)
    return df.div(first) * 100


# ---------------------------------------------------------------------------
# Sidebar — Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Marktvergleich")

    st.subheader("Zeitraum")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Von", value=date(2021, 1, 1))
    with c2:
        end_date = st.date_input("Bis", value=date.today())

    st.subheader("Darstellung")
    mode = st.radio("Kursmodus", ["Normiert (Basis 100)", "Absolut"], horizontal=True)
    show_event = st.toggle("📍 Kriegsbeginn (24.02.2022)", value=True)

    st.subheader("Indizes")
    selected_names: list[str] = []
    for region in REGIONS:
        icon = REGION_ICONS.get(region, "")
        st.markdown(f"**{icon} {region}**")
        for name, meta in INDICES.items():
            if meta["region"] != region:
                continue
            if st.checkbox(name, value=True, key=f"cb_{name}"):
                selected_names.append(name)

    st.divider()
    st.caption("ETF-Proxies wo kein direkter Index verfügbar.\nDaten: Yahoo Finance / yfinance.")

# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------
if not selected_names:
    st.title("🌍 Globaler Marktvergleich")
    st.info("Bitte mindestens einen Index in der Sidebar auswählen.")
    st.stop()

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
selected_tickers = tuple(INDICES[n]["ticker"] for n in selected_names)

with st.spinner("Kursdaten werden geladen …"):
    prices_raw = download_prices(
        tickers=selected_tickers,
        start=str(start_date),
        end=str(end_date),
    )

if prices_raw.empty:
    st.error("Keine Kursdaten geladen. Bitte Internetverbindung prüfen.")
    st.stop()

ticker_to_name = {INDICES[n]["ticker"]: n for n in selected_names}

available = [
    n for n in selected_names
    if INDICES[n]["ticker"] in prices_raw.columns
    and prices_raw[INDICES[n]["ticker"]].dropna().size > 10
]
missing = [n for n in selected_names if n not in available]

prices = prices_raw[[INDICES[n]["ticker"] for n in available]].copy()
prices.columns = [ticker_to_name[c] for c in prices.columns]
prices = prices.loc[str(start_date):str(end_date)]

plot_data = normalize(prices) if mode == "Normiert (Basis 100)" else prices

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------
st.title("🌍 Globaler Marktvergleich")
st.caption(
    f"Zeitraum: **{start_date.strftime('%d.%m.%Y')}** – **{end_date.strftime('%d.%m.%Y')}** · "
    f"Modus: **{mode}**"
)

if missing:
    st.warning(f"Nicht geladen (yfinance): {', '.join(missing)}")

fig = go.Figure()

for name in available:
    meta  = INDICES[name]
    y     = plot_data[name].dropna()
    dash  = "dot" if meta["note"].startswith("ETF") else "solid"

    fig.add_trace(go.Scatter(
        x=y.index,
        y=y.values,
        name=name,
        mode="lines",
        line=dict(color=meta["color"], width=2, dash=dash),
        hovertemplate=(
            f"<b>{name}</b><br>%{{x|%d.%m.%Y}}<br>"
            + ("%{y:.1f}" if mode == "Normiert (Basis 100)" else "%{y:,.0f}")
            + "<extra></extra>"
        ),
    ))

# War annotation — add_shape + add_annotation (add_vline ist mit Datetime-Achsen buggy)
if show_event and pd.Timestamp(start_date) <= EVENT_DATE <= pd.Timestamp(end_date):
    fig.add_shape(
        type="line",
        x0=EVENT_DATE_STR, x1=EVENT_DATE_STR,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="red", width=1.5, dash="dash"),
    )
    fig.add_annotation(
        x=EVENT_DATE_STR,
        y=0.97,
        xref="x", yref="paper",
        text="🔴 Kriegsbeginn<br>24.02.2022",
        showarrow=False,
        font=dict(size=11, color="red"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="red",
        borderwidth=1,
        xanchor="left",
    )

fig.update_layout(
    height=570,
    margin=dict(l=0, r=0, t=10, b=10),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.01,
        xanchor="left",  x=0,
        font=dict(size=11),
    ),
    xaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickformat="%b %Y"),
    yaxis=dict(
        showgrid=True,
        gridcolor="#F0F0F0",
        tickformat=".0f" if mode == "Normiert (Basis 100)" else ",.0f",
        title="Basis 100" if mode == "Normiert (Basis 100)" else "Kurs",
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Performance-Tabelle
# ---------------------------------------------------------------------------
rows = []
for name in available:
    col = prices[name].dropna()
    if len(col) < 2:
        continue

    perf_total = col.iloc[-1] / col.iloc[0] - 1

    nearest_after = col.index[col.index >= EVENT_DATE]
    if len(nearest_after):
        perf_war = col.iloc[-1] / col.loc[nearest_after[0]] - 1
    else:
        perf_war = np.nan

    rows.append({
        "Index":                        name,
        "Region":                       REGION_ICONS.get(INDICES[name]["region"], "") + " " + INDICES[name]["region"],
        "Gesamt-Performance":           perf_total,
        "Seit Kriegsbeginn (24.02.22)": perf_war,
        "Ticker":                       INDICES[name]["ticker"],
    })

if rows:
    df_perf = pd.DataFrame(rows).set_index("Index")
    st.dataframe(
        df_perf.style
            .format({
                "Gesamt-Performance":           "{:+.1%}",
                "Seit Kriegsbeginn (24.02.22)": "{:+.1%}",
            })
            .background_gradient(
                subset=["Gesamt-Performance", "Seit Kriegsbeginn (24.02.22)"],
                cmap="RdYlGn", vmin=-0.5, vmax=0.5,
            ),
        use_container_width=True,
        height=38 + len(rows) * 35,
    )

# ---------------------------------------------------------------------------
# ETF-Proxy-Legende
# ---------------------------------------------------------------------------
with st.expander("ℹ️ Verwendete Ticker & ETF-Proxies"):
    for name in available:
        meta = INDICES[name]
        st.markdown(f"- **{name}** → `{meta['ticker']}` — {meta['note']}")
