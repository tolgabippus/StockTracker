# config.py — edit here to change study setup
# All study parameters live here. Never hardcode dates or tickers elsewhere.

# ---------------------------------------------------------------------------
# Event definition
# ---------------------------------------------------------------------------
EVENT_DATE = "2022-02-24"          # The event date (T=0), Russia invades Ukraine

# Trading-day windows relative to T=0
ESTIMATION_WINDOW = (-250, -11)    # OLS regression window  (-250 to -11 trading days)
EVENT_WINDOW      = (-10, +10)     # AR / CAR window         (-10 to +10 trading days)

# ---------------------------------------------------------------------------
# Data download range
# Must fully cover both the estimation window and the event window.
# ---------------------------------------------------------------------------
START_DATE = "2021-01-01"          # Must reach back far enough for the estimation window
END_DATE   = "2023-12-31"          # Must extend past the end of the event window

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------
BENCHMARK = "^SXXP"               # STOXX Europe 600 — change to e.g. "^GSPC" for S&P 500

# ---------------------------------------------------------------------------
# Tickers
# ---------------------------------------------------------------------------
TICKERS = [
    "RBI.VI",   # Raiffeisen Bank International
    "UCG.MI",   # UniCredit
    "SHEL",     # Shell
    "TTE",      # TotalEnergies
    "SAP.DE",   # SAP
    "ASML.AS",  # ASML
    "MC.PA",    # LVMH
    # add more tickers here
]

# ---------------------------------------------------------------------------
# Miscellaneous
# ---------------------------------------------------------------------------
CURRENCY = "EUR"                   # For documentation only (no fx conversion yet)
MISSING_VALUE_STRATEGY = "ffill"   # "ffill" or "drop" — how to handle non-trading days

# ---------------------------------------------------------------------------
# Multiple event dates (optional extension)
# Uncomment and populate EVENT_DATES to loop over several events in 04_event_study.py
# ---------------------------------------------------------------------------
# EVENT_DATES = [
#     "2022-02-24",   # Russia invasion
#     "2022-03-04",   # Another event
# ]
