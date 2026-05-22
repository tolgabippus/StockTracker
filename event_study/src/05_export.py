"""
05_export.py — Assemble all results into a formatted Excel workbook.

Creates output/results.xlsx with the following sheets:

    Prices        — aligned adjusted close prices (all symbols)
    Returns       — daily log returns (all symbols)
    Market Model  — OLS parameters (alpha, beta, R², n_obs, SEs)
    AR            — abnormal returns per event day per ticker
    CAR           — cumulative abnormal returns + t-statistics
    Summary       — clean thesis-ready summary table

Run:
    python src/05_export.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

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
PROC_DIR      = ROOT / "data" / "processed"
OUTPUT_DIR    = ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PRICES_PATH   = PROC_DIR / "prices_aligned.csv"
RETURNS_PATH  = PROC_DIR / "returns.csv"
PARAMS_PATH   = PROC_DIR / "market_model_params.csv"
AR_PATH       = PROC_DIR / "abnormal_returns.csv"
CAR_PATH      = PROC_DIR / "car.csv"
OUTPUT_PATH   = OUTPUT_DIR / "results.xlsx"

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
HEADER_FILL  = PatternFill("solid", fgColor="1F4E79")   # dark blue
HEADER_FONT  = Font(color="FFFFFF", bold=True)
ACCENT_FILL  = PatternFill("solid", fgColor="D6E4F0")   # light blue for alternating rows
POSITIVE_FILL = PatternFill("solid", fgColor="C6EFCE")  # green
NEGATIVE_FILL = PatternFill("solid", fgColor="FFC7CE")  # red
BOLD         = Font(bold=True)

THIN = Side(style="thin")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _style_header_row(ws: Worksheet, row: int = 1) -> None:
    """Apply dark-blue header styling to all cells in a given row."""
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BORDER


def _autofit_columns(ws: Worksheet, min_width: int = 10, max_width: int = 30) -> None:
    """Set column widths based on content length."""
    for col_cells in ws.columns:
        max_len = max(
            (len(str(cell.value)) if cell.value is not None else 0)
            for cell in col_cells
        )
        col_letter = get_column_letter(col_cells[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, min_width), max_width)


def _freeze_header(ws: Worksheet, cell: str = "A2") -> None:
    """Freeze rows/columns above and to the left of `cell`."""
    ws.freeze_panes = cell


def load_all() -> dict[str, pd.DataFrame]:
    """Load all processed CSV files.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys: 'prices', 'returns', 'params', 'ar', 'car'.

    Raises
    ------
    FileNotFoundError
        If any required upstream file is missing.
    """
    required = {
        "prices":  PRICES_PATH,
        "returns": RETURNS_PATH,
        "params":  PARAMS_PATH,
        "ar":      AR_PATH,
        "car":     CAR_PATH,
    }
    data: dict[str, pd.DataFrame] = {}
    for key, path in required.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}. "
                "Run scripts 01–04 before exporting."
            )
        if key in ("prices", "returns"):
            data[key] = pd.read_csv(path, index_col="Date", parse_dates=True)
        elif key == "params":
            data[key] = pd.read_csv(path, index_col="ticker")
        elif key == "ar":
            data[key] = pd.read_csv(path, index_col="t")
        else:
            data[key] = pd.read_csv(path, index_col="ticker")
        log.info("Loaded %s: %s", key, data[key].shape)

    return data


def write_prices_sheet(writer: pd.ExcelWriter, prices: pd.DataFrame) -> None:
    """Write aligned prices to the 'Prices' sheet."""
    df = prices.copy()
    df.index = df.index.strftime("%Y-%m-%d")
    df = df.round(4)
    df.to_excel(writer, sheet_name="Prices")

    ws = writer.sheets["Prices"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws)
    log.info("Sheet 'Prices' written (%d rows).", len(df))


def write_returns_sheet(writer: pd.ExcelWriter, returns: pd.DataFrame) -> None:
    """Write daily log returns to the 'Returns' sheet."""
    df = returns.copy()
    df.index = df.index.strftime("%Y-%m-%d")
    df = df.round(6)
    df.to_excel(writer, sheet_name="Returns")

    ws = writer.sheets["Returns"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws)
    log.info("Sheet 'Returns' written (%d rows).", len(df))


def write_market_model_sheet(writer: pd.ExcelWriter, params: pd.DataFrame) -> None:
    """Write market model OLS parameters to the 'Market Model' sheet."""
    df = params.copy().round(6)

    # Rename columns for readability
    df.columns = [
        "Alpha (α)", "Beta (β)", "R²", "N (obs)",
        "SE Alpha", "SE Beta",
    ]
    df.index.name = "Ticker"
    df.to_excel(writer, sheet_name="Market Model")

    ws = writer.sheets["Market Model"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws)

    # Highlight high/low betas
    beta_col = 3  # column C (1-indexed: A=index, B=Alpha, C=Beta, …)
    for row_idx in range(2, len(df) + 2):
        cell = ws.cell(row=row_idx, column=beta_col)
        try:
            val = float(cell.value)
            if val > 1.2:
                cell.fill = NEGATIVE_FILL   # high systematic risk
            elif val < 0.5:
                cell.fill = POSITIVE_FILL   # low systematic risk
        except (TypeError, ValueError):
            pass

    log.info("Sheet 'Market Model' written.")


def write_ar_sheet(writer: pd.ExcelWriter, df_ar: pd.DataFrame) -> None:
    """Write abnormal returns to the 'AR' sheet with colour coding."""
    df = df_ar.copy()
    ticker_cols = [c for c in df.columns if c != "date"]

    # Round AR values
    df[ticker_cols] = df[ticker_cols].round(6)
    df.index.name   = "t (event day)"
    df.to_excel(writer, sheet_name="AR")

    ws = writer.sheets["AR"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws)

    # Colour-code positive / negative ARs
    date_col_offset = 2 if "date" in df.columns else 1
    for row_idx in range(2, len(df) + 2):
        for col_idx in range(date_col_offset + 1, date_col_offset + 1 + len(ticker_cols)):
            cell = ws.cell(row=row_idx, column=col_idx)
            try:
                val = float(cell.value)
                if val > 0:
                    cell.fill = POSITIVE_FILL
                elif val < 0:
                    cell.fill = NEGATIVE_FILL
            except (TypeError, ValueError):
                pass

    log.info("Sheet 'AR' written (%d event days × %d tickers).",
             len(df), len(ticker_cols))


def write_car_sheet(writer: pd.ExcelWriter, df_car: pd.DataFrame) -> None:
    """Write CAR results and significance to the 'CAR' sheet."""
    df = df_car.copy().round(6)
    df.index.name = "Ticker"

    rename_map = {
        "CAR":             "CAR",
        "t_stat":          "t-statistic",
        "p_value":         "p-value",
        "significant_5pct": "Significant (5%)",
        "mean_AR":         "Mean AR",
        "std_AR":          "Std AR",
        "n_days":          "N (days)",
    }
    df.rename(columns=rename_map, inplace=True)
    df.to_excel(writer, sheet_name="CAR")

    ws = writer.sheets["CAR"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws)

    # Highlight significant results
    for row_idx in range(2, len(df) + 2):
        sig_cell = ws.cell(row=row_idx, column=5)   # "Significant (5%)"
        car_cell = ws.cell(row=row_idx, column=2)   # "CAR"
        try:
            if sig_cell.value is True or str(sig_cell.value).lower() == "true":
                try:
                    car_val = float(car_cell.value)
                    fill = POSITIVE_FILL if car_val >= 0 else NEGATIVE_FILL
                except (TypeError, ValueError):
                    fill = POSITIVE_FILL
                for col in range(1, len(df.columns) + 2):
                    ws.cell(row=row_idx, column=col).fill = fill
        except (TypeError, ValueError):
            pass

    log.info("Sheet 'CAR' written.")


def build_summary(params: pd.DataFrame, df_car: pd.DataFrame) -> pd.DataFrame:
    """Create a clean thesis-ready summary table.

    Combines market model parameters with CAR results into a single table
    suitable for direct inclusion in a thesis or presentation.

    Parameters
    ----------
    params : pd.DataFrame
        Market model parameters indexed by ticker.
    df_car : pd.DataFrame
        CAR results indexed by ticker.

    Returns
    -------
    pd.DataFrame
        Summary table indexed by ticker.
    """
    summary = pd.DataFrame(index=config.TICKERS)
    summary.index.name = "Ticker"

    # Market model
    for ticker in summary.index:
        if ticker in params.index:
            summary.loc[ticker, "α (alpha)"]  = params.loc[ticker, "alpha"]
            summary.loc[ticker, "β (beta)"]   = params.loc[ticker, "beta"]
            summary.loc[ticker, "R²"]         = params.loc[ticker, "r_squared"]
        else:
            summary.loc[ticker, ["α (alpha)", "β (beta)", "R²"]] = np.nan

        if ticker in df_car.index:
            summary.loc[ticker, "CAR"]           = df_car.loc[ticker, "CAR"]
            summary.loc[ticker, "t-stat"]        = df_car.loc[ticker, "t_stat"]
            summary.loc[ticker, "p-value"]       = df_car.loc[ticker, "p_value"]
            summary.loc[ticker, "Sig. at 5%"]    = df_car.loc[ticker, "significant_5pct"]
        else:
            summary.loc[ticker, ["CAR", "t-stat", "p-value", "Sig. at 5%"]] = np.nan

    # Metadata
    summary.loc[:, "Event Date"]         = config.EVENT_DATE
    summary.loc[:, "Event Window"]       = f"[{config.EVENT_WINDOW[0]}, {config.EVENT_WINDOW[1]}]"
    summary.loc[:, "Estimation Window"]  = (
        f"[{config.ESTIMATION_WINDOW[0]}, {config.ESTIMATION_WINDOW[1]}]"
    )
    summary.loc[:, "Benchmark"]          = config.BENCHMARK

    return summary.round(6)


def write_summary_sheet(
    writer: pd.ExcelWriter,
    params: pd.DataFrame,
    df_car: pd.DataFrame,
) -> None:
    """Write the thesis-ready summary table to the 'Summary' sheet."""
    summary = build_summary(params, df_car)
    summary.to_excel(writer, sheet_name="Summary")

    ws = writer.sheets["Summary"]
    _style_header_row(ws)
    _freeze_header(ws)
    _autofit_columns(ws, max_width=35)

    # Highlight significant rows
    for row_idx in range(2, len(summary) + 2):
        sig_cell = ws.cell(row=row_idx, column=7)   # "Sig. at 5%" column
        try:
            if sig_cell.value is True or str(sig_cell.value).lower() == "true":
                sig_cell.font = Font(bold=True, color="006100")
        except (TypeError, ValueError):
            pass

    log.info("Sheet 'Summary' written.")


def main() -> None:
    """Entry point: load all data and write the Excel workbook."""
    log.info("=== 05_export.py — start ===")

    data = load_all()

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        write_prices_sheet(writer, data["prices"])
        write_returns_sheet(writer, data["returns"])
        write_market_model_sheet(writer, data["params"])
        write_ar_sheet(writer, data["ar"])
        write_car_sheet(writer, data["car"])
        write_summary_sheet(writer, data["params"], data["car"])

    log.info("Excel workbook saved → %s", OUTPUT_PATH)
    log.info("=== 05_export.py — done ===")


if __name__ == "__main__":
    main()
