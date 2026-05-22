"""
04_event_study.py — Compute Abnormal Returns (AR), CARs, and t-tests.

For each ticker and each day t in the EVENT_WINDOW:

    AR_{i,t} = R_{i,t} - (alpha_i + beta_i * R_{m,t})

Cumulative Abnormal Return over the full event window:

    CAR_i = sum_{t=t1}^{t2} AR_{i,t}

Significance is tested via a cross-sectional t-test (H0: mean CAR = 0).

Outputs:
    data/processed/abnormal_returns.csv  — AR per ticker per event day
    data/processed/car.csv               — CAR + individual ticker t-stats

Run:
    python src/04_event_study.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROC_DIR     = ROOT / "data" / "processed"
RETURNS_PATH = PROC_DIR / "returns.csv"
PARAMS_PATH  = PROC_DIR / "market_model_params.csv"
AR_PATH      = PROC_DIR / "abnormal_returns.csv"
CAR_PATH     = PROC_DIR / "car.csv"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load return series and market-model parameters from disk.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (returns, params) where returns has DatetimeIndex and params is
        indexed by ticker.

    Raises
    ------
    FileNotFoundError
        If either upstream script has not been run.
    """
    for path in (RETURNS_PATH, PARAMS_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}. "
                "Run 01_download.py → 02_returns.py → 03_market_model.py first."
            )

    returns = pd.read_csv(RETURNS_PATH, index_col="Date", parse_dates=True)
    params  = pd.read_csv(PARAMS_PATH, index_col="ticker")
    log.info("Loaded returns: %d rows × %d cols", *returns.shape)
    log.info("Loaded params for tickers: %s", list(params.index))
    return returns, params


def resolve_event_index(returns: pd.DataFrame) -> int:
    """Find integer position of the event date (T=0) in the return index.

    Searches forward up to 5 business days if the event falls on a
    non-trading day.

    Parameters
    ----------
    returns : pd.DataFrame
        Full return series with DatetimeIndex.

    Returns
    -------
    int
        Integer location of T=0 in the index.
    """
    event_date   = pd.Timestamp(config.EVENT_DATE)
    trading_days = returns.index

    if event_date in trading_days:
        return trading_days.get_loc(event_date)

    for offset in range(1, 6):
        candidate = event_date + pd.offsets.BDay(offset)
        if candidate in trading_days:
            log.warning(
                "EVENT_DATE %s is not a trading day — using %s.",
                event_date.date(), candidate.date(),
            )
            return trading_days.get_loc(candidate)

    raise ValueError(
        f"EVENT_DATE {event_date.date()} + 5 BDays not found in return series."
    )


def compute_abnormal_returns(
    returns: pd.DataFrame,
    params: pd.DataFrame,
    event_idx: int,
) -> pd.DataFrame:
    """Compute AR for every ticker over the event window.

    Parameters
    ----------
    returns : pd.DataFrame
        Full log-return series.
    params : pd.DataFrame
        Market-model parameters (alpha, beta) indexed by ticker.
    event_idx : int
        Integer position of T=0 in the return index.

    Returns
    -------
    pd.DataFrame
        AR values with relative event-day index (-10 … +10 by default)
        and one column per ticker.  The index is labelled "t" and the
        absolute trading date is stored in a "date" column.
    """
    t1, t2     = config.EVENT_WINDOW
    benchmark  = config.BENCHMARK

    start_pos = event_idx + t1
    end_pos   = event_idx + t2

    if start_pos < 0 or end_pos >= len(returns):
        raise ValueError(
            "EVENT_WINDOW extends outside the available return data. "
            "Adjust START_DATE, END_DATE, or EVENT_WINDOW."
        )

    event_returns = returns.iloc[start_pos : end_pos + 1]
    bench_event   = event_returns[benchmark]
    t_range       = range(t1, t2 + 1)

    ar_dict: dict[str, list[float]] = {}

    for ticker in config.TICKERS:
        if ticker not in params.index:
            log.warning("No market model params for %s — skipping.", ticker)
            continue
        if ticker not in returns.columns:
            log.warning("Ticker %s not in returns — skipping.", ticker)
            continue

        alpha = params.loc[ticker, "alpha"]
        beta  = params.loc[ticker, "beta"]

        expected = alpha + beta * bench_event
        actual   = event_returns[ticker]
        ar       = actual - expected

        ar_dict[ticker] = ar.values

    df_ar = pd.DataFrame(ar_dict, index=list(t_range))
    df_ar.index.name = "t"

    # Store absolute dates for readability in Excel
    df_ar.insert(0, "date", event_returns.index)

    log.info(
        "Computed AR for %d tickers over t=%d..%d (%d days).",
        len(ar_dict), t1, t2, len(df_ar),
    )
    return df_ar


def compute_car(df_ar: pd.DataFrame) -> pd.DataFrame:
    """Aggregate AR to CAR and compute individual-ticker t-statistics.

    The t-statistic for ticker i tests H0: CAR_i = 0 using the time-series
    standard deviation of daily ARs (Patell / standardised-residual approach
    simplified to equal weights):

        t_i = CAR_i / (std(AR_{i,t}) * sqrt(T))

    where T is the number of event-window days.

    Parameters
    ----------
    df_ar : pd.DataFrame
        AR DataFrame as returned by compute_abnormal_returns (index = t).

    Returns
    -------
    pd.DataFrame
        One row per ticker with columns:
        CAR, t_stat, p_value, significant_5pct, mean_AR, std_AR, n_days.
    """
    ticker_cols = [c for c in df_ar.columns if c != "date"]
    ar_only     = df_ar[ticker_cols]

    records = []
    for ticker in ticker_cols:
        ar_series = ar_only[ticker].dropna()
        n         = len(ar_series)
        car       = ar_series.sum()
        std_ar    = ar_series.std(ddof=1)

        if std_ar == 0 or n < 2:
            t_stat  = np.nan
            p_value = np.nan
        else:
            t_stat  = car / (std_ar * np.sqrt(n))
            p_value = 2 * stats.t.sf(abs(t_stat), df=n - 1)

        records.append({
            "ticker":          ticker,
            "CAR":             car,
            "t_stat":          t_stat,
            "p_value":         p_value,
            "significant_5pct": (p_value < 0.05) if not np.isnan(p_value) else False,
            "mean_AR":         ar_series.mean(),
            "std_AR":          std_ar,
            "n_days":          n,
        })

    df_car = pd.DataFrame(records).set_index("ticker")

    # Cross-sectional summary (pooled test across tickers)
    cars       = df_car["CAR"].dropna()
    n_tickers  = len(cars)
    mean_car   = cars.mean()
    std_car    = cars.std(ddof=1)
    if std_car > 0 and n_tickers > 1:
        cs_t    = mean_car / (std_car / np.sqrt(n_tickers))
        cs_p    = 2 * stats.t.sf(abs(cs_t), df=n_tickers - 1)
    else:
        cs_t = cs_p = np.nan

    log.info("CAR results:")
    log.info("\n%s", df_car.to_string())
    log.info(
        "Cross-sectional test — mean CAR=%.4f  t=%.3f  p=%.4f  (n=%d tickers)",
        mean_car, cs_t, cs_p, n_tickers,
    )

    return df_car


def main() -> None:
    """Entry point: compute AR and CAR, save to CSVs."""
    log.info("=== 04_event_study.py — start ===")

    returns, params = load_data()
    event_idx       = resolve_event_index(returns)

    df_ar  = compute_abnormal_returns(returns, params, event_idx)
    df_car = compute_car(df_ar)

    df_ar.to_csv(AR_PATH)
    log.info("Saved abnormal returns → %s", AR_PATH)

    df_car.to_csv(CAR_PATH)
    log.info("Saved CAR results      → %s", CAR_PATH)

    log.info("=== 04_event_study.py — done ===")


if __name__ == "__main__":
    main()
