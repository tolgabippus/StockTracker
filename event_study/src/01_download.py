"""
01_download.py — Download raw Adj Close prices via yfinance.

Downloads daily Adjusted Close prices for every ticker in TICKERS plus the
BENCHMARK index for the date range [START_DATE, END_DATE] and writes the
result to data/raw/prices_raw.csv.

Run:
    python src/01_download.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Path setup — allow running from any working directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402  (import after sys.path patch)

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
# Output paths
# ---------------------------------------------------------------------------
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = RAW_DIR / "prices_raw.csv"


def download_ticker(ticker: str, start: str, end: str) -> pd.Series | None:
    """Download Adj Close prices for a single ticker.

    Parameters
    ----------
    ticker : str
        Yahoo Finance ticker symbol.
    start : str
        Start date in YYYY-MM-DD format.
    end : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    pd.Series or None
        Daily Adjusted Close prices indexed by date, or None on failure.
    """
    try:
        log.info("Downloading %s …", ticker)
        raw = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=True,   # gives adjusted OHLCV; "Close" == adj close
            progress=False,
        )
        if raw.empty:
            log.warning("No data returned for %s — skipping.", ticker)
            return None

        # yfinance ≥0.2 may return a MultiIndex column when auto_adjust=True
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
            if isinstance(close, pd.DataFrame):
                # single-ticker download returns DataFrame with one column
                close = close.iloc[:, 0]
        else:
            close = raw["Close"]

        close.name = ticker
        log.info("  %s — %d rows (%s → %s)", ticker, len(close),
                 close.index.min().date(), close.index.max().date())
        return close

    except Exception as exc:
        log.error("Failed to download %s: %s", ticker, exc)
        return None


def download_all() -> pd.DataFrame:
    """Download prices for all configured tickers and the benchmark.

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with one column per symbol and dates as the index.
        Symbols that failed to download are omitted; a warning is logged for each.
    """
    all_symbols = [config.BENCHMARK] + config.TICKERS
    series_list: list[pd.Series] = []
    failed: list[str] = []

    for symbol in all_symbols:
        s = download_ticker(symbol, config.START_DATE, config.END_DATE)
        if s is not None:
            series_list.append(s)
        else:
            failed.append(symbol)

    if not series_list:
        raise RuntimeError("All downloads failed — check your internet connection.")

    df = pd.concat(series_list, axis=1, sort=True)
    df.index.name = "Date"

    if failed:
        log.warning("The following symbols could NOT be downloaded: %s", failed)
    else:
        log.info("All %d symbols downloaded successfully.", len(all_symbols))

    return df


def main() -> None:
    """Entry point: download prices and save to CSV."""
    log.info("=== 01_download.py — start ===")
    log.info("Event date : %s", config.EVENT_DATE)
    log.info("Date range : %s → %s", config.START_DATE, config.END_DATE)
    log.info("Benchmark  : %s", config.BENCHMARK)
    log.info("Tickers    : %s", config.TICKERS)

    df = download_all()

    df.to_csv(OUTPUT_PATH)
    log.info("Saved %d rows × %d columns to %s", *df.shape, OUTPUT_PATH)
    log.info("=== 01_download.py — done ===")


if __name__ == "__main__":
    main()
