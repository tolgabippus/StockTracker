"""
app.py — Globaler Marktvergleich

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

ROOT      = Path(__file__).resolve().parent
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
# Global CSS — Clean White Design
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Font & base */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
    color: #111827;
}

/* White background */
.stApp { background-color: #FFFFFF; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #F8FAFC !important;
    border-right: 1px solid #E2E8F0 !important;
    padding-top: 1.5rem !important;
}
[data-testid="stSidebar"] section { padding: 0 1rem !important; }

/* Sidebar section labels (subheader) */
[data-testid="stSidebar"] h3 {
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    color: #9CA3AF !important;
    margin-top: 1.4rem !important;
    margin-bottom: 0.25rem !important;
}

/* Sidebar title */
[data-testid="stSidebar"] h2 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin-bottom: 0.25rem !important;
}

/* ── Headings ── */
h1 {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 0.1rem !important;
}
h2 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    letter-spacing: -0.01em !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 6px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border: 1px solid #D1D5DB !important;
    background: #FFFFFF !important;
    color: #374151 !important;
    padding: 0.35rem 0.9rem !important;
    transition: border-color 0.15s, color 0.15s !important;
}
.stButton > button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background: #FFFFFF !important;
}
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    border-radius: 6px !important;
    font-weight: 500 !important;
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
}
.stDownloadButton > button:hover {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ── Radio & Checkbox ── */
[data-testid="stRadio"] label    { font-size: 0.875rem !important; color: #374151 !important; }
[data-testid="stCheckbox"] label { font-size: 0.85rem !important;  color: #374151 !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] label { font-size: 0.875rem !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid #F1F5F9 !important; margin: 1.5rem 0 !important; }

/* ── Caption ── */
.stCaption p { color: #9CA3AF !important; font-size: 0.775rem !important; line-height: 1.5 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 6px !important; }

/* ── Expander ── */
details { border: 1px solid #E5E7EB !important; border-radius: 6px !important; }
summary { font-size: 0.875rem !important; font-weight: 500 !important; color: #374151 !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] iframe { border-radius: 6px !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { font-size: 0.875rem !important; color: #6B7280 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Index definitions
# ─────────────────────────────────────────────────────────────────────────────
INDICES: dict[str, dict] = {
    "Euro STOXX 50": {
        "ticker": "^STOXX50E", "region": "Europa",
        "note": "Index direkt", "color": "#1E3A8A",
    },
    "STOXX Europe 600": {
        "ticker": "EXSA.DE", "region": "Europa",
        "note": "ETF-Proxy: iShares STOXX Europe 600 UCITS ETF", "color": "#2563EB",
    },
    "MSCI EM Eastern Europe ex Russia": {
        "ticker": "CE9.DE", "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Eastern Europe Capped", "color": "#60A5FA",
    },
    "STOXX Eastern Europe Large 100": {
        "ticker": "EPOL", "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Poland ETF", "color": "#93C5FD",
    },
    "MSCI Europe Small Cap": {
        "ticker": "IEUS", "region": "Europa",
        "note": "ETF-Proxy: iShares MSCI Europe Small-Cap ETF", "color": "#BFDBFE",
    },
    "Dow Jones Industrial": {
        "ticker": "^DJI", "region": "Amerika",
        "note": "Index direkt", "color": "#991B1B",
    },
    "NASDAQ Composite": {
        "ticker": "^IXIC", "region": "Amerika",
        "note": "Index direkt", "color": "#EF4444",
    },
    "S&P Asia 50": {
        "ticker": "AIA", "region": "Asien",
        "note": "ETF-Proxy: iShares S&P Asia 50 ETF", "color": "#065F46",
    },
    "MSCI AC Asia": {
        "ticker": "AAXJ", "region": "Asien",
        "note": "ETF-Proxy: iShares MSCI All Country Asia ex Japan ETF", "color": "#10B981",
    },
    "MSCI Australia Large Cap": {
        "ticker": "EWA", "region": "Australien",
        "note": "ETF-Proxy: iShares MSCI Australia ETF", "color": "#D97706",
    },
}

REGIONS    = sorted({v["region"] for v in INDICES.values()})
EVENT_DATE = pd.Timestamp("2022-02-24")
EVENT_STR  = "2022-02-24"


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def download_prices(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    """Download adjusted close prices for each ticker individually."""
    frames: list[pd.Series] = []
    for ticker in tickers:
        try:
            raw = yf.download(ticker, start=start, end=end,
                              auto_adjust=True, progress=False)
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
    """Batch download for constituent stocks."""
    try:
        raw = yf.download(list(tickers), start=start, end=end,
                          auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        return close.ffill()
    except Exception:
        return pd.DataFrame()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    first = df.apply(lambda c: c.dropna().iloc[0] if c.dropna().size else np.nan)
    return df.div(first) * 100


def section(title: str) -> None:
    """Render a clean section header with a blue left border."""
    st.markdown(
        f"""<div style="border-left:3px solid #2563EB; padding-left:10px;
                        margin:1.8rem 0 0.6rem 0;">
              <span style="font-size:0.95rem; font-weight:600;
                           color:#111827; letter-spacing:-0.01em;">{title}</span>
            </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='margin-bottom:4px'>Marktvergleich</h2>"
        "<p style='font-size:0.775rem;color:#9CA3AF;margin-bottom:1rem'>"
        "Globale Indexperformance seit 2021</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='margin:0 0 1rem 0'>", unsafe_allow_html=True)

    st.subheader("Zeitraum")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Von", value=date(2021, 1, 1),
                                   label_visibility="visible")
    with c2:
        end_date = st.date_input("Bis", value=date.today(),
                                 label_visibility="visible")

    st.subheader("Darstellung")
    mode = st.radio("Modus", ["Normiert (Basis 100)", "Absolut"],
                    horizontal=True, label_visibility="collapsed")
    show_event = st.checkbox("Kriegsbeginn markieren (24.02.2022)", value=True)

    st.subheader("Indizes")
    selected_names: list[str] = []
    for region in REGIONS:
        st.markdown(
            f"<p style='font-size:0.75rem;font-weight:600;color:#6B7280;"
            f"margin:0.9rem 0 0.2rem 0;text-transform:uppercase;"
            f"letter-spacing:0.07em'>{region}</p>",
            unsafe_allow_html=True,
        )
        for name, meta in INDICES.items():
            if meta["region"] != region:
                continue
            if st.checkbox(name, value=True, key=f"cb_{name}"):
                selected_names.append(name)

    st.markdown("<hr style='margin:1.2rem 0 0.8rem 0'>", unsafe_allow_html=True)

    # STOXX 600 full list status
    if _FULL_JSON.exists():
        _n = json.loads(_FULL_JSON.read_text()).get("count", "?")
        st.markdown(
            f"<p style='font-size:0.775rem;color:#059669;font-weight:500'>"
            f"STOXX 600 vollständig geladen ({_n} Aktien)</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p style='font-size:0.775rem;color:#D97706;font-weight:500'>"
            "STOXX 600: Fallback-Liste aktiv (~272 Aktien)</p>",
            unsafe_allow_html=True,
        )
        if st.button("Vollständige Liste laden", use_container_width=True):
            with st.spinner("Lade STOXX 600 Konstituenten ..."):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "src" / "00_fetch_constituents.py")],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            if result.returncode == 0:
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Laden fehlgeschlagen.")
                st.code(result.stderr[-1000:])

    st.markdown(
        "<p style='font-size:0.72rem;color:#D1D5DB;margin-top:0.5rem'>"
        "Kursdaten: Yahoo Finance</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Guard
# ─────────────────────────────────────────────────────────────────────────────
if not selected_names:
    st.title("Globaler Marktvergleich")
    st.info("Bitte mindestens einen Index in der Sidebar auswählen.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Download index prices
# ─────────────────────────────────────────────────────────────────────────────
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

prices = prices_raw[[INDICES[n]["ticker"] for n in available]].copy()
prices.columns = [ticker_to_name[c] for c in prices.columns]
prices = prices.loc[str(start_date):str(end_date)]
plot_data = normalize(prices) if mode == "Normiert (Basis 100)" else prices


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1>Globaler Marktvergleich</h1>"
    f"<p style='font-size:0.875rem;color:#6B7280;margin-top:2px;margin-bottom:1rem'>"
    f"{start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;{mode}</p>",
    unsafe_allow_html=True,
)

if missing:
    st.warning(f"Nicht verfügbar: {', '.join(missing)}")


# ─────────────────────────────────────────────────────────────────────────────
# Index chart
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()

for name in available:
    meta = INDICES[name]
    y    = plot_data[name].dropna()
    fig.add_trace(go.Scatter(
        x=y.index, y=y.values,
        name=name, mode="lines",
        line=dict(
            color=meta["color"], width=2,
            dash="dot" if meta["note"].startswith("ETF") else "solid",
        ),
        hovertemplate=(
            f"<b>{name}</b><br>%{{x|%d.%m.%Y}}<br>"
            + ("%{y:.1f}" if "Normiert" in mode else "%{y:,.0f}")
            + "<extra></extra>"
        ),
    ))

if show_event and pd.Timestamp(start_date) <= EVENT_DATE <= pd.Timestamp(end_date):
    fig.add_shape(
        type="line",
        x0=EVENT_STR, x1=EVENT_STR, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="#EF4444", width=1.2, dash="dash"),
    )
    fig.add_annotation(
        x=EVENT_STR, y=0.97, xref="x", yref="paper",
        text="Kriegsbeginn<br>24.02.2022",
        showarrow=False,
        font=dict(size=10, color="#EF4444"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#EF4444",
        borderwidth=1,
        borderpad=4,
        xanchor="left",
    )

fig.update_layout(
    height=520,
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    legend=dict(
        orientation="h", y=1.02, x=0,
        yanchor="bottom", xanchor="left",
        font=dict(size=11, color="#374151"),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        showgrid=True, gridcolor="#F3F4F6",
        tickformat="%b %Y", tickfont=dict(size=11, color="#6B7280"),
        zeroline=False,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#F3F4F6",
        tickformat=".0f" if "Normiert" in mode else ",.0f",
        tickfont=dict(size=11, color="#6B7280"),
        title=dict(text="Basis 100" if "Normiert" in mode else "Kurs",
                   font=dict(size=11, color="#9CA3AF")),
        zeroline=False,
    ),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
)
st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Performance table (indices)
# ─────────────────────────────────────────────────────────────────────────────
rows = []
war_in_range = pd.Timestamp(end_date) >= EVENT_DATE

for name in available:
    col = prices[name].dropna()
    if len(col) < 2:
        continue
    perf_total = col.iloc[-1] / col.iloc[0] - 1
    nearest = col.index[col.index >= EVENT_DATE]
    perf_war = (col.iloc[-1] / col.loc[nearest[0]] - 1) if len(nearest) else np.nan
    rows.append({
        "Index":            name,
        "Region":           INDICES[name]["region"],
        "Performance":      perf_total,
        "Seit 24.02.2022":  perf_war,
        "Typ":              "Direkt" if INDICES[name]["note"] == "Index direkt" else "ETF-Proxy",
    })

if rows:
    df_perf = pd.DataFrame(rows).set_index("Index")
    if not war_in_range:
        df_perf = df_perf.drop(columns=["Seit 24.02.2022"])
        st.caption("Enddatum liegt vor dem 24.02.2022 — Kriegsbeginn-Spalte nicht verfügbar.")

    fmt = {"Performance": "{:+.1%}"}
    grad = ["Performance"]
    if war_in_range:
        fmt["Seit 24.02.2022"] = "{:+.1%}"
        grad.append("Seit 24.02.2022")

    st.dataframe(
        df_perf.style
            .format(fmt, na_rep="—")
            .background_gradient(subset=grad, cmap="RdYlGn", vmin=-0.5, vmax=0.5),
        use_container_width=True,
        height=38 + len(rows) * 35,
    )

with st.expander("Datenquellen & Ticker"):
    for name in available:
        meta = INDICES[name]
        st.markdown(f"**{name}** — `{meta['ticker']}` — {meta['note']}")


# ─────────────────────────────────────────────────────────────────────────────
# Einzelaktien
# ─────────────────────────────────────────────────────────────────────────────
section("Einzelaktien")

STOXX50_SET = set(STOXX50_TICKERS)

ca, cb = st.columns([3, 1])
with ca:
    idx_choice = st.radio(
        "Index",
        [f"Euro STOXX 50  ({len(STOXX50_TICKERS)} Aktien)",
         f"STOXX Europe 600  ({len(STOXX600_TICKERS)} Aktien)"],
        horizontal=True,
        label_visibility="collapsed",
    )
with cb:
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

load_key = f"loaded_{idx_choice}"
if load_key not in st.session_state:
    st.session_state[load_key] = False

if not st.session_state[load_key]:
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

        perf_rows = []
        for ticker in valid:
            col = prices_c[ticker].dropna()
            if len(col) < 2:
                continue

            perf_total = col.iloc[-1] / col.iloc[0] - 1
            nearest    = col.index[col.index >= EVENT_DATE]
            perf_war   = (col.iloc[-1] / col.loc[nearest[0]] - 1) if len(nearest) else np.nan

            r = r_all[ticker].dropna() if ticker in r_all else pd.Series(dtype=float)
            ev = r.index[(r.index >= EVENT_DATE) &
                         (r.index <= EVENT_DATE + pd.Timedelta(days=4))]
            r_event = float(r.loc[ev[0]]) if len(ev) else np.nan

            pre   = r[r.index < EVENT_DATE].tail(60)
            r_mu  = pre.mean() if len(pre) > 10 else np.nan
            r_sig = pre.std(ddof=1) if len(pre) > 10 else np.nan
            ar    = (r_event - r_mu) if not np.isnan(r_event) and not np.isnan(r_mu) else np.nan
            z     = (ar / r_sig) if (r_sig and r_sig > 0 and not np.isnan(ar)) else np.nan

            if np.isnan(z):      signal = "—"
            elif abs(z) > 3:     signal = "Extrem"
            elif abs(z) > 2:     signal = "Signifikant"
            else:                signal = "Normal"

            perf_rows.append({
                "Ticker":           ticker,
                "Performance":      perf_total,
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

            # ── Bar chart ──────────────────────────────────────────────────
            colors = ["#16A34A" if v >= 0 else "#DC2626"
                      for v in df_c["Performance"]]
            fig_c = go.Figure(go.Bar(
                x=df_c.index, y=df_c["Performance"],
                marker_color=colors,
                text=[f"{v:+.1%}" for v in df_c["Performance"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y:+.1%}<extra></extra>",
            ))
            fig_c.add_hline(y=0, line_color="#E5E7EB", line_width=1)
            fig_c.update_layout(
                height=380,
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(tickformat=".0%", showgrid=True,
                           gridcolor="#F3F4F6", zeroline=False,
                           tickfont=dict(size=10, color="#6B7280")),
                xaxis=dict(showgrid=False,
                           tickfont=dict(size=9, color="#6B7280")),
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                showlegend=False,
            )
            st.plotly_chart(fig_c, use_container_width=True)

            # ── Table ──────────────────────────────────────────────────────
            fmt   = {"Performance": "{:+.1%}"}
            grad  = ["Performance"]
            drops = []

            if pd.Timestamp(end_date) >= EVENT_DATE:
                fmt["Seit 24.02.2022"] = "{:+.1%}"
                grad.append("Seit 24.02.2022")
            else:
                drops.append("Seit 24.02.2022")

            if ar_available:
                fmt["Return 24.02.22"]   = "{:+.2%}"
                fmt["Abnormale Rendite"] = "{:+.2%}"
                fmt["Z-Score"]           = "{:.2f}"
                grad += ["Return 24.02.22", "Abnormale Rendite"]
            else:
                drops += ["Return 24.02.22", "Abnormale Rendite", "Z-Score", "Signal"]

            df_c = df_c.drop(columns=[c for c in drops if c in df_c.columns])

            st.dataframe(
                df_c.style
                    .format(fmt, na_rep="—")
                    .background_gradient(subset=grad, cmap="RdYlGn",
                                         vmin=-0.15, vmax=0.15),
                use_container_width=True,
                height=min(38 + len(df_c) * 35, 600),
            )

            if ar_available:
                st.caption(
                    "Abnormale Rendite = tatsächlicher Return am 24.02.22 minus "
                    "durchschnittlicher Return der 60 Handelstage davor.  "
                    "Signal: Signifikant |Z| > 2 · Extrem |Z| > 3"
                )

            st.caption(
                f"{len(valid)} von {len(const_tickers)} Aktien geladen · "
                f"{section_label} · {start_date} – {end_date}"
            )

            if st.button("Neu laden"):
                st.session_state[load_key] = False
                st.cache_data.clear()
                st.rerun()

            # ── Excel export ───────────────────────────────────────────────
            section("Excel-Export")

            ea, eb, ec = st.columns([3, 1, 1])
            with ea:
                export_sel = st.multiselect(
                    "Aktien",
                    options=list(df_c.index),
                    default=[],
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

            perf_exp_rows = []
            for t in tickers_exp_ok:
                ct = prices_exp[t].dropna()
                if len(ct) < 2:
                    continue
                near = ct.index[ct.index >= EVENT_DATE]
                perf_exp_rows.append({
                    "Ticker":           t,
                    "Performance":      ct.iloc[-1] / ct.iloc[0] - 1,
                    "Seit 24.02.2022":  (ct.iloc[-1] / ct.loc[near[0]] - 1) if len(near) else np.nan,
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

            st.download_button(
                label=f"Download  —  {len(tickers_exp_ok)} Aktien  ·  "
                      f"{exp_start.strftime('%d.%m.%Y')} – {exp_end.strftime('%d.%m.%Y')}",
                data=buf.getvalue(),
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
            st.caption("3 Sheets: Preise · Renditen (logarithmisch) · Performance")
