"""
03_market_model.py — Estimate the market model via OLS (estimation window).

For each ticker we run:

    R_{i,t} = alpha_i + beta_i * R_{m,t} + epsilon_{i,t}

where the regression is fitted over the ESTIMATION_WINDOW only.

Output saved to data/processed/market_model_params.csv with columns:
    ticker, alpha, beta, r_squared, n_obs, se_alpha, se_beta

Run:
    python src/03_market_model.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import statsmodels.api as sm

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
RETURNS_PATH = ROOT / "data" / "processed" / "returns.csv"
PROC_DIR     = ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)
PARAMS_PATH  = PROC_DIR / "market_model_params.csv"


def load_returns() -> pd.DataFrame:
    """Load the aligned log-return series from disk.

    Returns
    -------
    pd.DataFrame
        Log returns with DatetimeIndex.

    Raises
    ------
    FileNotFoundError
        If 02_returns.py has not been run yet.
    """
    if not RETURNS_PATH.exists():
        raise FileNotFoundError(
            f"Returns file not found at {RETURNS_PATH}. "
            "Run 02_returns.py first."
        )
    df = pd.read_csv(RETURNS_PATH, index_col="Date", parse_dates=True)
    log.info("Loaded returns: %d rows × %d columns", *df.shape)
    return df


def resolve_event_index(returns: pd.DataFrame) -> int:
    """Find the integer position of the event date in the returns index.

    Because markets may be closed on EVENT_DATE itself we search for the
    nearest available trading date on or after the event.

    Parameters
    ----------
    returns : pd.DataFrame
        Full return series with DatetimeIndex.

    Returns
    -------
    int
        Integer location of the event date (or the first date after it).

    Raises
    ------
    ValueError
        If the event date falls outside the data range entirely.
    """
    event_date = pd.Timestamp(config.EVENT_DATE)
    trading_days = returns.index

    if event_date in trading_days:
        idx = trading_days.get_loc(event_date)
        log.info("Event date %s found at position %d in return series.", event_date.date(), idx)
        return idx

    # Search forward up to 5 trading days
    for offset in range(1, 6):
        candidate = event_date + pd.offsets.BDay(offset)
        if candidate in trading_days:
            idx = trading_days.get_loc(candidate)
            log.warning(
                "Event date %s is not a trading day — using next available date %s (position %d).",
                event_date.date(), candidate.date(), idx,
            )
            return idx

    raise ValueError(
        f"Event date {event_date.date()} and the 5 following business days "
        "are all absent from the return series. Check START_DATE / END_DATE."
    )


def get_window_dates(
    returns: pd.DataFrame,
    event_idx: int,
    window: tuple[int, int],
    label: str,
) -> pd.DatetimeIndex:
    """Extract the DatetimeIndex for a given window.

    Parameters
    ----------
    returns : pd.DataFrame
        Full return series.
    event_idx : int
        Integer position of T=0 in the index.
    window : tuple[int, int]
        (start_offset, end_offset) in trading days relative to T=0.
    label : str
        Human-readable label for logging.

    Returns
    -------
    pd.DatetimeIndex
        Trading dates within the window.
    """
    start_pos = event_idx + window[0]
    end_pos   = event_idx + window[1]

    if start_pos < 0:
        raise ValueError(
            f"{label} start ({window[0]}) exceeds available history. "
            "Extend START_DATE or reduce |ESTIMATION_WINDOW[0]|."
        )
    if end_pos >= len(returns):
        raise ValueError(
            f"{label} end ({window[1]}) exceeds available data. "
            "Extend END_DATE."
        )

    dates = returns.index[start_pos : end_pos + 1]
    log.info("%s: %s → %s (%d days)", label, dates[0].date(), dates[-1].date(), len(dates))
    return dates


def fit_market_model(
    ticker_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict:
    """Fit OLS market model for a single ticker over the estimation window.

    Parameters
    ----------
    ticker_returns : pd.Series
        Stock log returns during the estimation window.
    benchmark_returns : pd.Series
        Benchmark log returns during the estimation window.

    Returns
    -------
    dict
        Keys: alpha, beta, r_squared, n_obs, se_alpha, se_beta.
    """
    X = sm.add_constant(benchmark_returns, has_constant="add")
    result = sm.OLS(ticker_returns, X).fit()

    return {
        "alpha":     result.params["const"],
        "beta":      result.params[benchmark_returns.name],
        "r_squared": result.rsquared,
        "n_obs":     int(result.nobs),
        "se_alpha":  result.bse["const"],
        "se_beta":   result.bse[benchmark_returns.name],
    }


def estimate_all(returns: pd.DataFrame) -> pd.DataFrame:
    """Run OLS market model for every ticker in the returns DataFrame.

    Parameters
    ----------
    returns : pd.DataFrame
        Full return series (benchmark + tickers).

    Returns
    -------
    pd.DataFrame
        One row per ticker with columns: alpha, beta, r_squared, n_obs,
        se_alpha, se_beta.
    """
    event_idx  = resolve_event_index(returns)
    est_dates  = get_window_dates(returns, event_idx, config.ESTIMATION_WINDOW, "Estimation window")
    benchmark  = config.BENCHMARK

    if benchmark not in returns.columns:
        raise KeyError(
            f"Benchmark '{benchmark}' not found in returns. "
            "Check BENCHMARK in config.py and re-run 01_download.py."
        )

    bench_est = returns.loc[est_dates, benchmark]
    records   = []

    for ticker in config.TICKERS:
        if ticker not in returns.columns:
            log.warning("Ticker %s not in returns — skipping.", ticker)
            continue

        stock_est = returns.loc[est_dates, ticker].dropna()

        # Align benchmark to the same dates (handles any residual NaN rows)
        aligned_bench = bench_est.loc[stock_est.index].dropna()
        stock_est     = stock_est.loc[aligned_bench.index]

        if len(stock_est) < 30:
            log.warning(
                "Ticker %s has only %d observations in estimation window — "
                "results may be unreliable.",
                ticker, len(stock_est),
            )

        params = fit_market_model(stock_est, aligned_bench)
        params["ticker"] = ticker
        records.append(params)

        log.info(
            "  %s — alpha=%.5f  beta=%.4f  R²=%.4f  n=%d",
            ticker, params["alpha"], params["beta"], params["r_squared"], params["n_obs"],
        )

    df_params = pd.DataFrame(records).set_index("ticker")
    return df_params


def main() -> None:
    """Entry point: estimate market model parameters and save to CSV."""
    log.info("=== 03_market_model.py — start ===")

    returns   = load_returns()
    df_params = estimate_all(returns)

    df_params.to_csv(PARAMS_PATH)
    log.info("Saved market model parameters → %s", PARAMS_PATH)
    log.info("\n%s", df_params.to_string())
    log.info("=== 03_market_model.py — done ===")


if __name__ == "__main__":
    main()
