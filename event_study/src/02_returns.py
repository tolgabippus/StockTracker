"""
02_returns.py — Align prices and compute daily log returns.

Reads the raw price CSV produced by 01_download.py, aligns all tickers to a
common set of trading days (inner join), handles missing values according to
MISSING_VALUE_STRATEGY, then computes daily log returns:

    r_t = ln(P_t / P_{t-1})

Output is saved to data/processed/returns.csv.

Run:
    python src/02_returns.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd

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
RAW_PATH  = ROOT / "data" / "raw"       / "prices_raw.csv"
PROC_DIR  = ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)
RETURNS_PATH  = PROC_DIR / "returns.csv"
PRICES_PATH   = PROC_DIR / "prices_aligned.csv"


def load_raw_prices() -> pd.DataFrame:
    """Load raw price CSV from disk.

    Returns
    -------
    pd.DataFrame
        Wide-format prices with DatetimeIndex.
    """
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Raw prices not found at {RAW_PATH}. "
            "Run 01_download.py first."
        )
    df = pd.read_csv(RAW_PATH, index_col="Date", parse_dates=True)
    log.info("Loaded raw prices: %d rows × %d columns", *df.shape)
    return df


def align_trading_days(df: pd.DataFrame) -> pd.DataFrame:
    """Align all series to the intersection of their trading days.

    Different exchanges observe different public holidays.  We keep only
    dates for which ALL columns have an observation (inner join).  This
    is the most conservative approach and avoids introducing look-ahead
    or backward-fill artefacts into the return series.

    Parameters
    ----------
    df : pd.DataFrame
        Raw prices, potentially with NaNs on exchange-specific holidays.

    Returns
    -------
    pd.DataFrame
        Prices restricted to dates present for every column.
    """
    strategy = config.MISSING_VALUE_STRATEGY.lower()

    if strategy == "ffill":
        # Forward-fill each column independently before taking the union of
        # trading days (so a stock that was closed on a given day inherits
        # the previous day's close, matching standard event-study practice).
        df = df.ffill()
        log.info("Applied forward-fill for missing values.")
    elif strategy == "drop":
        # Drop any row that has at least one NaN — keeps only dates on which
        # every exchange was open.
        before = len(df)
        df = df.dropna()
        log.info("Dropped %d rows with NaN values (drop strategy).", before - len(df))
    else:
        raise ValueError(
            f"Unknown MISSING_VALUE_STRATEGY '{strategy}'. "
            "Use 'ffill' or 'drop'."
        )

    # After filling / dropping, ensure the index is sorted
    df = df.sort_index()

    # Final sanity check — no NaNs allowed downstream
    remaining = df.isna().sum().sum()
    if remaining:
        log.warning(
            "%d NaN cells remain after alignment — consider switching to 'ffill'.",
            remaining,
        )

    return df


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily log returns from price levels.

    r_t = ln(P_t / P_{t-1})

    The first row is dropped because it has no prior day.

    Parameters
    ----------
    prices : pd.DataFrame
        Aligned price levels with DatetimeIndex.

    Returns
    -------
    pd.DataFrame
        Daily log returns, same shape minus the first row.
    """
    returns = np.log(prices / prices.shift(1)).dropna(how="all")
    log.info(
        "Computed log returns: %d trading days × %d series",
        *returns.shape,
    )
    return returns


def main() -> None:
    """Entry point: load raw prices, align, compute returns, save."""
    log.info("=== 02_returns.py — start ===")

    prices_raw = load_raw_prices()
    prices     = align_trading_days(prices_raw)
    returns    = compute_log_returns(prices)

    # Persist aligned prices (useful for 05_export.py)
    prices.to_csv(PRICES_PATH)
    log.info("Saved aligned prices → %s", PRICES_PATH)

    returns.to_csv(RETURNS_PATH)
    log.info("Saved log returns    → %s", RETURNS_PATH)

    # Quick diagnostics
    log.info("Return period: %s → %s",
             returns.index.min().date(), returns.index.max().date())
    log.info("Columns: %s", list(returns.columns))
    log.info("=== 02_returns.py — done ===")


if __name__ == "__main__":
    main()
