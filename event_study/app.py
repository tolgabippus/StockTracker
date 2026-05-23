"""
app.py — Globaler Marktvergleich

Start:
    streamlit run app.py
"""

import sys
from datetime import date
from pathlib import Path

import importlib
import io
import json
import subprocess

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

import data.constituents as _constituents_mod
from data.constituents import STOXX50_TICKERS

ROOT = Path(__file__).resolve().parent
_FULL_JSON = ROOT / "data" / "stoxx600_full_tickers.json"


def _get_stoxx600() -> list[str]:
    """Lade STOXX600-Liste — bevorzugt die volle JSON, sonst Fallback."""
    if _FULL_JSON.exists():
        return json.loads(_FULL_JSON.read_text())["tickers"]
    importlib.reload(_constituents_mod)
    return _constituents_mod.STOXX600_TICKERS


STOXX600_TICKERS = _get_stoxx600()

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


@st.cache_data(show_spinner=False, ttl=3600)
def download_constituents_batch(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    """Batch-Download für Einzelaktien (schneller als Einzelabruf)."""
    try:
        raw = yf.download(
            list(tickers), start=start, end=end,
            auto_adjust=True, progress=False,
        )
        if raw.empty:
            return pd.DataFrame()
        # yfinance gibt bei mehreren Tickern MultiIndex zurück: (OHLCV, Ticker)
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        return close.ffill()
    except Exception:
        return pd.DataFrame()


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

    # ── STOXX 600 vollständige Liste ────────────────────────────────────────
    if _FULL_JSON.exists():
        _n = json.loads(_FULL_JSON.read_text()).get("count", "?")
        st.success(f"✅ STOXX 600 vollständig: {_n} Aktien")
    else:
        st.warning("⚠️ STOXX 600: nur ~272 Aktien (Fallback-Liste)")
        if st.button("🔄 Volle STOXX 600 Liste laden (iShares)", use_container_width=True):
            with st.spinner("Hole alle 600 Konstituenten von iShares …"):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "src" / "00_fetch_constituents.py")],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            if result.returncode == 0:
                st.success("✅ Fertig! Seite wird neu geladen …")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Fehler beim Laden:")
                st.code(result.stderr[-1500:])

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

    war_in_range = pd.Timestamp(end_date) >= EVENT_DATE

    if war_in_range:
        style = (
            df_perf.style
                .format({
                    "Gesamt-Performance":           "{:+.1%}",
                    "Seit Kriegsbeginn (24.02.22)": "{:+.1%}",
                }, na_rep="—")
                .background_gradient(
                    subset=["Gesamt-Performance", "Seit Kriegsbeginn (24.02.22)"],
                    cmap="RdYlGn", vmin=-0.5, vmax=0.5,
                )
        )
    else:
        # Enddatum liegt vor dem Kriegsbeginn → Spalte weglassen
        df_perf = df_perf.drop(columns=["Seit Kriegsbeginn (24.02.22)"])
        style = (
            df_perf.style
                .format({"Gesamt-Performance": "{:+.1%}"})
                .background_gradient(
                    subset=["Gesamt-Performance"],
                    cmap="RdYlGn", vmin=-0.5, vmax=0.5,
                )
        )
        st.caption("ℹ️ Enddatum liegt vor dem 24.02.2022 — Kriegsbeginn-Spalte nicht verfügbar.")

    st.dataframe(style, use_container_width=True, height=38 + len(rows) * 35)

# ---------------------------------------------------------------------------
# ETF-Proxy-Legende
# ---------------------------------------------------------------------------
with st.expander("ℹ️ Verwendete Ticker & ETF-Proxies"):
    for name in available:
        meta = INDICES[name]
        st.markdown(f"- **{name}** → `{meta['ticker']}` — {meta['note']}")

# ---------------------------------------------------------------------------
# Einzelaktien — STOXX 50 / STOXX 600
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📊 Einzelaktien")

# Ticker-Auswahl
STOXX50_SET  = set(STOXX50_TICKERS)
STOXX600_EXTRA = [t for t in STOXX600_TICKERS if t not in STOXX50_SET]

c_left, c_right = st.columns([3, 1])
with c_left:
    idx_choice = st.radio(
        "Index",
        [f"🔵 Euro STOXX 50  ({len(STOXX50_TICKERS)} Aktien)",
         f"🟠 STOXX Europe 600  ({len(STOXX600_TICKERS)} Aktien)"],
        horizontal=True,
        label_visibility="collapsed",
    )
with c_right:
    sort_dir = st.selectbox("Sortierung", ["Performance ↓", "Performance ↑", "A–Z"],
                            label_visibility="collapsed")

if "STOXX 50" in idx_choice:
    const_tickers = tuple(STOXX50_TICKERS)
    section_label = "Euro STOXX 50"
else:
    const_tickers = tuple(STOXX600_TICKERS)   # alle ~250 Konstituenten
    section_label = "STOXX Europe 600 (alle Konstituenten)"

# Lazy-Load Button damit nicht jede Sidebar-Änderung 50 Aktien neu lädt
load_key = f"loaded_{idx_choice}"
if load_key not in st.session_state:
    st.session_state[load_key] = False

if not st.session_state[load_key]:
    if st.button(f"📥 {section_label} laden ({len(const_tickers)} Aktien)", type="primary"):
        st.session_state[load_key] = True
        st.rerun()
    st.caption("Erster Ladevorgang dauert ca. 15–30 Sekunden. Danach gecacht (1 h).")
else:
    with st.spinner(f"Lade {len(const_tickers)} Aktien …"):
        const_raw = download_constituents_batch(
            tickers=const_tickers,
            start=str(start_date),
            end=str(end_date),
        )

    if const_raw.empty:
        st.warning("Keine Kursdaten geladen — bitte Internetverbindung prüfen.")
    else:
        # Nur Tickers mit genug Daten behalten
        valid = [c for c in const_raw.columns if const_raw[c].dropna().size > 10]
        prices_c = const_raw[valid].loc[str(start_date):str(end_date)]

        # Tägliche Log-Renditen (für AR-Berechnung)
        r_daily_all = np.log(prices_c / prices_c.shift(1)).dropna(how="all")

        # Performance + Abnormale Rendite am Ereignistag
        perf_rows = []
        for ticker in valid:
            col = prices_c[ticker].dropna()
            if len(col) < 2:
                continue

            perf_total = col.iloc[-1] / col.iloc[0] - 1
            nearest    = col.index[col.index >= EVENT_DATE]
            perf_war   = (col.iloc[-1] / col.loc[nearest[0]] - 1) if len(nearest) else np.nan

            # Tatsächliche Rendite am Ereignistag (oder nächster Handelstag)
            r_daily = r_daily_all[ticker].dropna() if ticker in r_daily_all else pd.Series(dtype=float)
            ev_days = r_daily.index[(r_daily.index >= EVENT_DATE) &
                                    (r_daily.index <= EVENT_DATE + pd.Timedelta(days=4))]
            r_event = float(r_daily.loc[ev_days[0]]) if len(ev_days) else np.nan

            # Schätzfenster: 60 Handelstage vor Ereignis
            pre = r_daily[r_daily.index < EVENT_DATE].tail(60)
            r_mu  = pre.mean() if len(pre) > 10 else np.nan
            r_sig = pre.std(ddof=1) if len(pre) > 10 else np.nan

            # Abnormale Rendite = tatsächlich − erwartet (mean-adjusted)
            ar_event = (r_event - r_mu) if not np.isnan(r_event) and not np.isnan(r_mu) else np.nan
            z_score  = (ar_event / r_sig) if (r_sig and r_sig > 0
                                               and not np.isnan(ar_event)) else np.nan

            # Ampel-Flag
            if np.isnan(z_score):
                flag = "—"
            elif abs(z_score) > 3:
                flag = "🚨 extrem"
            elif abs(z_score) > 2:
                flag = "⚠️ signifikant"
            else:
                flag = "✅ normal"

            perf_rows.append({
                "Ticker":                       ticker,
                "Gesamt-Performance":           perf_total,
                "Seit Kriegsbeginn (24.02.22)": perf_war,
                "Return 24.02.22":              r_event,
                "Abnormale Rendite (AR)":       ar_event,
                "Z-Score":                      z_score,
                "Signal":                       flag,
            })

        if not perf_rows:
            st.warning("Keine auswertbaren Kursdaten.")
        else:
            df_c = pd.DataFrame(perf_rows).set_index("Ticker")

            # Sortierung
            if sort_dir == "Performance ↓":
                df_c = df_c.sort_values("Gesamt-Performance", ascending=False)
            elif sort_dir == "Performance ↑":
                df_c = df_c.sort_values("Gesamt-Performance", ascending=True)
            else:
                df_c = df_c.sort_index()

            # ── Balkendiagramm ──────────────────────────────────────────────
            colors = ["#2ecc71" if v >= 0 else "#e74c3c"
                      for v in df_c["Gesamt-Performance"]]

            fig_c = go.Figure(go.Bar(
                x=df_c.index,
                y=df_c["Gesamt-Performance"],
                marker_color=colors,
                text=[f"{v:+.1%}" for v in df_c["Gesamt-Performance"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y:+.1%}<extra></extra>",
            ))
            fig_c.add_hline(y=0, line_color="black", line_width=0.8)
            fig_c.update_layout(
                height=420,
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(
                    tickformat=".0%",
                    title="Gesamt-Performance",
                    showgrid=True, gridcolor="#F0F0F0",
                ),
                xaxis=dict(showgrid=False),
                plot_bgcolor="white",
                paper_bgcolor="white",
                showlegend=False,
            )
            st.plotly_chart(fig_c, use_container_width=True)

            # ── Tabelle ─────────────────────────────────────────────────────
            war_ok = pd.Timestamp(end_date) >= EVENT_DATE

            # AR-Spalten nur zeigen wenn Ereignistag im Zeitraum liegt
            ar_cols_available = (
                pd.Timestamp(start_date) <= EVENT_DATE <= pd.Timestamp(end_date)
            )

            fmt = {"Gesamt-Performance": "{:+.1%}"}
            grad_cols = ["Gesamt-Performance"]
            drop_cols = []

            if war_ok:
                fmt["Seit Kriegsbeginn (24.02.22)"] = "{:+.1%}"
                grad_cols.append("Seit Kriegsbeginn (24.02.22)")
            else:
                drop_cols.append("Seit Kriegsbeginn (24.02.22)")

            if ar_cols_available:
                fmt["Return 24.02.22"]        = "{:+.2%}"
                fmt["Abnormale Rendite (AR)"] = "{:+.2%}"
                fmt["Z-Score"]                = "{:.2f}"
                grad_cols += ["Return 24.02.22", "Abnormale Rendite (AR)"]
            else:
                drop_cols += ["Return 24.02.22", "Abnormale Rendite (AR)",
                              "Z-Score", "Signal"]

            if drop_cols:
                df_c = df_c.drop(columns=[c for c in drop_cols if c in df_c.columns])

            st.dataframe(
                df_c.style
                    .format(fmt, na_rep="—")
                    .background_gradient(
                        subset=grad_cols, cmap="RdYlGn",
                        vmin=-0.15, vmax=0.15,
                    ),
                use_container_width=True,
                height=min(38 + len(df_c) * 35, 650),
            )

            if ar_cols_available:
                st.caption(
                    "**Abnormale Rendite (AR)** = Return am 24.02.22 − ∅ Return "
                    "(60 Handelstage vor Ereignis, mean-adjusted Modell)  ·  "
                    "⚠️ |Z| > 2  ·  🚨 |Z| > 3"
                )

            st.caption(
                f"✅ {len(valid)} von {len(const_tickers)} Tickern geladen · "
                f"{section_label} · Zeitraum: {start_date} – {end_date}"
            )

            if st.button("🔄 Neu laden"):
                st.session_state[load_key] = False
                st.cache_data.clear()
                st.rerun()

            # ── Excel-Export ────────────────────────────────────────────────
            st.divider()
            st.subheader("📤 Excel-Export")

            exp_a, exp_b, exp_c_col = st.columns([3, 1, 1])
            with exp_a:
                export_sel = st.multiselect(
                    "Aktien auswählen (leer = alle)",
                    options=list(df_c.index),
                    default=[],
                    placeholder=f"Alle {len(df_c)} Aktien",
                )
            with exp_b:
                exp_start = st.date_input("Von", value=start_date,  key="exp_s")
            with exp_c_col:
                exp_end   = st.date_input("Bis", value=end_date,    key="exp_e")

            # Welche Tickers exportieren?
            tickers_exp = export_sel if export_sel else list(df_c.index)
            tickers_exp_ok = [t for t in tickers_exp if t in prices_c.columns]

            # Preise im gewählten Zeitraum
            prices_exp = prices_c[tickers_exp_ok].loc[str(exp_start):str(exp_end)]

            # Log-Renditen
            returns_exp = np.log(prices_exp / prices_exp.shift(1)).dropna(how="all")

            # Performance-Tabelle für Export-Auswahl neu berechnen
            perf_rows_exp = []
            for t in tickers_exp_ok:
                col_t = prices_exp[t].dropna()
                if len(col_t) < 2:
                    continue
                p_total = col_t.iloc[-1] / col_t.iloc[0] - 1
                near = col_t.index[col_t.index >= EVENT_DATE]
                p_war = (col_t.iloc[-1] / col_t.loc[near[0]] - 1) if len(near) else np.nan
                perf_rows_exp.append({
                    "Ticker": t,
                    "Gesamt-Performance": p_total,
                    "Seit Kriegsbeginn (24.02.22)": p_war,
                    "Von": str(exp_start),
                    "Bis": str(exp_end),
                })
            df_exp_perf = pd.DataFrame(perf_rows_exp).set_index("Ticker") if perf_rows_exp else pd.DataFrame()

            # Excel in Buffer schreiben
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                # Preise
                prices_exp.round(4).to_excel(writer, sheet_name="Preise")
                # Log-Renditen
                returns_exp.round(6).to_excel(writer, sheet_name="Renditen")
                # Performance-Übersicht
                if not df_exp_perf.empty:
                    df_exp_perf.style \
                        .format({
                            "Gesamt-Performance":           "{:+.2%}",
                            "Seit Kriegsbeginn (24.02.22)": "{:+.2%}",
                        }, na_rep="—") \
                        .to_excel(writer, sheet_name="Performance")

            filename = (
                f"stoxx_{section_label.split()[1].lower()}_"
                f"{exp_start}_{exp_end}.xlsx"
            ).replace(" ", "_")

            st.download_button(
                label=(
                    f"📥 Excel herunterladen  —  "
                    f"{len(tickers_exp_ok)} Aktien  ·  "
                    f"{exp_start.strftime('%d.%m.%Y')} – {exp_end.strftime('%d.%m.%Y')}"
                ),
                data=buf.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
            st.caption("Enthält 3 Sheets: **Preise** · **Renditen** (Log) · **Performance**")
