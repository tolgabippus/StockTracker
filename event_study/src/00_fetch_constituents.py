"""
00_fetch_constituents.py — Alle 600 STOXX-Europe-600-Konstituenten herunterladen.

Quelle: iShares STOXX Europe 600 UCITS ETF (EXSA.DE) — tägliche Holdings-CSV.
Konvertiert Börsenkürzel + Exchange-Code → yfinance-kompatible Ticker.
Speichert das Ergebnis in data/stoxx600_full_tickers.json.

Einmalig ausführen (danach gecacht):
    python src/00_fetch_constituents.py
"""

import io
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

OUTPUT_PATH = ROOT / "data" / "stoxx600_full_tickers.json"

# ---------------------------------------------------------------------------
# iShares Holdings URLs (Fallback-Kette)
# ---------------------------------------------------------------------------
ISHARES_URLS = [
    # UK/EU iShares STOXX Europe 600 UCITS ETF (EXSA)
    (
        "https://www.ishares.com/uk/individual/en/products/251904/"
        "ISHARES-STOXX-EUROPE-600-UCITS-ETF/1478358645587.ajax"
        "?fileType=csv&fileName=EXSA_holdings&dataType=fund"
    ),
    # Alternative: Swiss domain
    (
        "https://www.ishares.com/ch/individual/en/products/251904/"
        "ISHARES-STOXX-EUROPE-600-UCITS-ETF/1478358645587.ajax"
        "?fileType=csv&fileName=EXSA_holdings&dataType=fund"
    ),
]

# ---------------------------------------------------------------------------
# Exchange → yfinance-Suffix
# ---------------------------------------------------------------------------
EXCHANGE_SUFFIX: dict[str, str] = {
    # Deutschland
    "XETR": ".DE",
    "XFRA": ".F",
    # Frankreich
    "XPAR": ".PA",
    # Niederlande
    "XAMS": ".AS",
    # Großbritannien
    "XLON": ".L",
    # Italien
    "XMIL": ".MI",
    # Spanien
    "XMAD": ".MC",
    # Schweiz
    "XSWX": ".SW",
    "XVTX": ".SW",
    # Schweden
    "XSTO": ".ST",
    # Dänemark
    "XCSE": ".CO",
    # Finnland
    "XHEL": ".HE",
    # Norwegen
    "XOSL": ".OL",
    # Belgien
    "XBRU": ".BR",
    # Österreich
    "XWBO": ".VI",
    # Portugal
    "XLIS": ".LS",
    # Irland
    "XDUB": ".IR",
    # Polen
    "XWAR": ".WA",
    # Ungarn
    "XBUD": ".BD",
    # Tschechien
    "XPRA": ".PR",
    # Luxemburg
    "XLUX": ".LU",
    # Griechenland
    "ASEX": ".AT",
}

# Ticker-Korrekturen für bekannte yfinance-Abweichungen
MANUAL_OVERRIDES: dict[str, str] = {
    "SHEL.L":    "SHEL",       # Shell: yfinance bevorzugt US-Format
    "AZN.L":     "AZN",        # AstraZeneca
    "ULVR.L":    "ULVR.L",
    "GSK.L":     "GSK",
    "BP.L":      "BP",
    "RIO.L":     "RIO",
    "HSBA.L":    "HSBA.L",
    "DGE.L":     "DGE.L",
    "REL.L":     "REL.L",
    "EXPN.L":    "EXPN.L",
    "CRH.L":     "CRH",
    "LSEG.L":    "LSEG.L",
    "FLTR.L":    "FLTR.L",
    "BA.L":      "BA.L",
    "NXT.L":     "NXT.L",
    "VOD.L":     "VOD",
    "LIN.DE":    "LIN",        # Linde: US-Primärlisting
    "NFLX.CO":   "NOVO-B.CO",  # war placeholder in manueller Liste
    "TTE":       "TTE",        # TotalEnergies: kein Suffix nötig
}


def build_yfinance_ticker(raw_ticker: str, exchange: str) -> str | None:
    """Konvertiere iShares-Ticker + Exchange-Code → yfinance-Ticker.

    Parameters
    ----------
    raw_ticker : str
        Rohes Börsenkürzel aus der iShares-CSV.
    exchange : str
        Exchange-Code (z.B. 'XETR', 'XPAR').

    Returns
    -------
    str or None
        yfinance-kompatibler Ticker oder None wenn nicht mappbar.
    """
    if not raw_ticker or raw_ticker.lower() in ("nan", "-", ""):
        return None

    suffix  = EXCHANGE_SUFFIX.get(exchange.upper(), "")
    yf_tick = (raw_ticker + suffix).upper()

    # Manuelle Korrekturen anwenden
    return MANUAL_OVERRIDES.get(yf_tick, yf_tick)


def fetch_ishares_holdings() -> pd.DataFrame | None:
    """Versuche, die iShares Holdings-CSV herunterzuladen.

    Returns
    -------
    pd.DataFrame or None
        Rohes DataFrame der Holdings oder None bei Fehler.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    for url in ISHARES_URLS:
        try:
            log.info("Versuche URL: %s", url[:80] + "…")
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()

            # iShares CSVs haben typischerweise 2 Header-Zeilen
            text = resp.text
            for skip in (2, 1, 0):
                try:
                    df = pd.read_csv(io.StringIO(text), skiprows=skip)
                    # Prüfen ob Mindest-Spalten vorhanden
                    if {"Ticker", "Exchange"}.issubset(set(df.columns)):
                        log.info("CSV erfolgreich geparst (skiprows=%d, %d Zeilen).", skip, len(df))
                        return df
                    # Alternativ englische Spaltennamen
                    if {"Asset Class", "Name"}.issubset(set(df.columns)):
                        log.info("CSV gefunden aber Spalten-Mapping unklar — zeige Spalten:")
                        log.info(list(df.columns))
                        return df
                except Exception:
                    continue

        except requests.RequestException as exc:
            log.warning("URL fehlgeschlagen: %s — %s", url[:60], exc)

    return None


def parse_tickers(df: pd.DataFrame) -> list[str]:
    """Extrahiere und konvertiere alle Equity-Tickers aus dem Holdings-DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Rohes iShares-Holdings-DataFrame.

    Returns
    -------
    list[str]
        Deduplizierte Liste yfinance-kompatibler Ticker.
    """
    log.info("DataFrame-Spalten: %s", list(df.columns))

    # Spalten flexibel suchen (iShares ändert manchmal die Benennung)
    ticker_col   = next((c for c in df.columns if "ticker"   in c.lower()), None)
    exchange_col = next((c for c in df.columns if "exchange" in c.lower()), None)
    asset_col    = next((c for c in df.columns if "asset"    in c.lower() and "class" in c.lower()), None)

    if not ticker_col or not exchange_col:
        log.error("Benötigte Spalten 'Ticker' / 'Exchange' nicht gefunden.")
        log.error("Verfügbare Spalten: %s", list(df.columns))
        return []

    tickers: list[str] = []
    skipped = 0

    for _, row in df.iterrows():
        # Nur Aktien
        if asset_col:
            asset_class = str(row.get(asset_col, "")).strip().lower()
            if asset_class not in ("equity", "aktie", "stock"):
                skipped += 1
                continue

        raw_ticker = str(row[ticker_col]).strip()
        exchange   = str(row[exchange_col]).strip()

        yf_ticker = build_yfinance_ticker(raw_ticker, exchange)
        if yf_ticker:
            tickers.append(yf_ticker)

    log.info("Extrahiert: %d Aktien-Ticker (%d andere Positionen übersprungen).",
             len(tickers), skipped)

    # Deduplizieren, Reihenfolge beibehalten
    return list(dict.fromkeys(tickers))


def main() -> None:
    """Entry point: fetch, parse, save."""
    log.info("=== 00_fetch_constituents.py — start ===")

    df = fetch_ishares_holdings()

    if df is None:
        log.error(
            "iShares-Download fehlgeschlagen.\n"
            "Mögliche Ursachen:\n"
            "  • iShares hat die URL geändert\n"
            "  • Kein Internetzugang\n"
            "  • Geo-Blocking\n\n"
            "Manueller Fallback: Lade die Holdings-CSV direkt von\n"
            "  https://www.ishares.com/uk/individual/en/products/251904\n"
            "und speichere sie als data/stoxx600_manual.csv, dann passe\n"
            "dieses Skript an."
        )
        sys.exit(1)

    tickers = parse_tickers(df)

    if len(tickers) < 100:
        log.warning(
            "Nur %d Ticker gefunden — das ist weniger als erwartet. "
            "CSV-Format hat sich möglicherweise geändert.", len(tickers)
        )

    # Speichern
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps({"tickers": tickers, "count": len(tickers)}, indent=2)
    )
    log.info("Gespeichert: %d Ticker → %s", len(tickers), OUTPUT_PATH)
    log.info("=== 00_fetch_constituents.py — done ===")


if __name__ == "__main__":
    main()
