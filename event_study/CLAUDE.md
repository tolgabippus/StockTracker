# Event Study Pipeline — CLAUDE.md

## Project Summary
A modular, reproducible Event Study pipeline for a Bachelor Thesis.
Computes Abnormal Returns (AR), Cumulative Abnormal Returns (CAR),
and exports everything to a formatted Excel workbook.

## Quick Start
```bash
pip install -r requirements.txt
python src/01_download.py
python src/02_returns.py
python src/03_market_model.py
python src/04_event_study.py
python src/05_export.py
# → output/results.xlsx
```

## Config
**All parameters live in `config.py`** — never hardcode anything in src/.
- Change event date → `EVENT_DATE`
- Change tickers    → `TICKERS`
- Change benchmark  → `BENCHMARK`
- Change windows    → `ESTIMATION_WINDOW` / `EVENT_WINDOW`

## Module Map
| Script | Input | Output |
|--------|-------|--------|
| 01_download.py | config | data/raw/prices_raw.csv |
| 02_returns.py | prices_raw.csv | prices_aligned.csv, returns.csv |
| 03_market_model.py | returns.csv | market_model_params.csv |
| 04_event_study.py | returns.csv + params | abnormal_returns.csv, car.csv |
| 05_export.py | all of the above | output/results.xlsx |

## Coding Standards
- Python 3.10+  •  pandas / numpy / scipy / statsmodels / yfinance / openpyxl
- All scripts runnable standalone: `python src/<script>.py`
- `sys.path` trick for config import — no relative imports
- `logging` not `print`
- Every function has a docstring
- yfinance failures handled gracefully (log + continue)

## Key Decisions
- **Log returns**: `ln(P_t / P_{t-1})` — standard in academic event studies
- **Missing values**: configurable `ffill` (default) or `drop`
- **t-test**: time-series std of ARs within event window (Patell-style simplified)
- **Cross-sectional test**: mean CAR / (std / sqrt(n)) across tickers
- **Benchmark**: STOXX Europe 600 (`^SXXP`) — change in config.py

## Known Limitations
- yfinance is unofficial — cross-check data manually if in doubt
- No FX conversion — mixing EUR/USD/GBP tickers makes CARs non-comparable
- Forward-fill is a simplification — document in thesis
- Adj Close retroactively adjusts for splits/dividends — re-download if needed
