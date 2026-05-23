"""
00_fetch_constituents.py — Alle 600 STOXX-Europe-600-Konstituenten herunterladen.

Strategie (in Reihenfolge):
  1. Produktseite parsen → echte Download-URL dynamisch extrahieren
  2. Bekannte Fallback-URLs probieren (verschiedene iShares-Domains)
  3. Klare Fehlermeldung wenn alles fehlschlägt

Einmalig ausführen (danach gecacht):
    python src/00_fetch_constituents.py
"""

import io
import json
import logging
import re
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
# Konstanten
# ---------------------------------------------------------------------------
PRODUCT_PAGES = [
    "https://www.ishares.com/uk/individual/en/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF",
    "https://www.ishares.com/uk/intermediaries/en/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF",
    "https://www.ishares.com/de/privatanleger/de/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF",
    "https://www.ishares.com/ch/individual/en/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF",
]

# Fallback: hart-kodierte URLs für bekannte iShares-Timestamp-Varianten
FALLBACK_URLS = [
    # Timestamp 2016 (original)
    "https://www.ishares.com/uk/individual/en/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF/1478358645587.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
    "https://www.ishares.com/uk/intermediaries/en/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF/1478358645587.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
    "https://www.ishares.com/de/privatanleger/de/products/251904/ISHARES-STOXX-EUROPE-600-UCITS-ETF/1478358645587.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
]

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# ---------------------------------------------------------------------------
# Exchange → yfinance-Suffix
# ---------------------------------------------------------------------------
EXCHANGE_SUFFIX: dict[str, str] = {
    "XETR": ".DE", "XFRA": ".F",
    "XPAR": ".PA",
    "XAMS": ".AS",
    "XLON": ".L",
    "XMIL": ".MI",
    "XMAD": ".MC",
    "XSWX": ".SW", "XVTX": ".SW",
    "XSTO": ".ST",
    "XCSE": ".CO",
    "XHEL": ".HE",
    "XOSL": ".OL",
    "XBRU": ".BR",
    "XWBO": ".VI",
    "XLIS": ".LS",
    "XDUB": ".IR",
    "XWAR": ".WA",
    "XBUD": ".BD",
    "XPRA": ".PR",
    "XLUX": ".LU",
    "ASEX": ".AT",
}

MANUAL_OVERRIDES: dict[str, str] = {
    "SHEL.L": "SHEL",
    "AZN.L":  "AZN",
    "GSK.L":  "GSK",
    "BP.L":   "BP",
    "RIO.L":  "RIO",
    "CRH.L":  "CRH",
    "VOD.L":  "VOD",
    "LIN.DE": "LIN",
    "TTE":    "TTE",
    "NFLX.CO": "NOVO-B.CO",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_yfinance_ticker(raw_ticker: str, exchange: str) -> str | None:
    if not raw_ticker or raw_ticker.lower() in ("nan", "-", ""):
        return None
    suffix = EXCHANGE_SUFFIX.get(exchange.upper(), "")
    yf_tick = (raw_ticker + suffix).upper()
    return MANUAL_OVERRIDES.get(yf_tick, yf_tick)


def _try_parse_csv(text: str) -> pd.DataFrame | None:
    """Versuche CSV mit verschiedenen skiprows-Werten zu parsen."""
    for skip in (2, 1, 0):
        try:
            df = pd.read_csv(io.StringIO(text), skiprows=skip)
            cols = set(df.columns)
            if {"Ticker", "Exchange"}.issubset(cols):
                log.info("CSV geparst (skiprows=%d, %d Zeilen).", skip, len(df))
                return df
            if {"Asset Class", "Name"}.issubset(cols):
                log.info("CSV gefunden, Spalten: %s", list(df.columns))
                return df
        except Exception:
            continue
    return None


def _fetch_url(session: requests.Session, url: str, referer: str = "") -> pd.DataFrame | None:
    """Versuche eine CSV-URL zu laden und zu parsen."""
    headers = {
        **BROWSER_HEADERS,
        "Accept": "text/csv,text/plain,application/csv,*/*",
    }
    if referer:
        headers["Referer"] = referer
    try:
        resp = session.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            log.warning("HTTP %d für %s", resp.status_code, url[:70])
            return None
        df = _try_parse_csv(resp.text)
        if df is not None:
            return df
        log.warning("Kein verwertbares CSV-Format in der Antwort.")
    except Exception as exc:
        log.warning("Fehler beim Laden: %s — %s", url[:70], exc)
    return None


# ---------------------------------------------------------------------------
# Strategie 1: Download-URL dynamisch aus Produktseite extrahieren
# ---------------------------------------------------------------------------
def discover_download_url(session: requests.Session, product_page: str) -> str | None:
    """Lade die Produktseite und extrahiere die echte CSV-Download-URL.

    iShares ändert gelegentlich den Timestamp im URL-Pfad. Diese Funktion
    findet die aktuelle URL automatisch im HTML der Produktseite.
    """
    log.info("Lese Produktseite: %s", product_page[:80])
    try:
        resp = session.get(
            product_page,
            headers={**BROWSER_HEADERS, "Accept": "text/html,*/*"},
            timeout=20,
        )
        if resp.status_code != 200:
            log.warning("Produktseite: HTTP %d", resp.status_code)
            return None

        html = resp.text

        # Muster 1: vollständige URL mit .ajax und fileType=csv
        patterns = [
            r'(https://www\.ishares\.com[^"\'\\]+251904[^"\'\\]+\.ajax[^"\'\\]*fileType=csv[^"\'\\]*)',
            r'(/[a-z/]+/products/251904/[^"\'\\]+\.ajax[^"\'\\]*fileType=csv[^"\'\\]*)',
            r'(https://www\.ishares\.com[^"\'\\]+251904[^"\'\\]+holdings[^"\'\\]*\.csv[^"\'\\]*)',
            # JSON-Daten im Script-Tag
            r'"downloadUrl"\s*:\s*"([^"]+251904[^"]+fileType=csv[^"]+)"',
            r'"csvUrl"\s*:\s*"([^"]+251904[^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                url = matches[0].replace("\\u0026", "&").replace("\\/", "/")
                if not url.startswith("http"):
                    url = "https://www.ishares.com" + url
                log.info("Download-URL gefunden: %s", url[:90])
                return url

        log.warning("Keine Download-URL im HTML der Produktseite gefunden.")
        log.debug("HTML-Länge: %d Zeichen", len(html))

    except Exception as exc:
        log.warning("Produktseite nicht erreichbar: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Haupt-Fetch-Funktion
# ---------------------------------------------------------------------------
def fetch_ishares_holdings() -> pd.DataFrame | None:
    """Lade die iShares STOXX Europe 600 Holdings.

    Reihenfolge:
      1. Jede Produktseite besuchen → URL dynamisch extrahieren → CSV laden
      2. Fallback-URLs (hartcodierte Varianten) probieren
    """
    session = requests.Session()

    # ── Strategie 1: Dynamische URL-Entdeckung ──────────────────────────────
    for product_page in PRODUCT_PAGES:
        download_url = discover_download_url(session, product_page)
        if download_url:
            df = _fetch_url(session, download_url, referer=product_page)
            if df is not None:
                return df
            log.warning("URL gefunden, aber CSV-Download fehlgeschlagen.")

    # ── Strategie 2: Fallback-URLs ───────────────────────────────────────────
    log.info("Versuche Fallback-URLs …")
    for url in FALLBACK_URLS:
        log.info("Fallback: %s", url[:80])
        df = _fetch_url(session, url)
        if df is not None:
            return df

    return None


# ---------------------------------------------------------------------------
# Ticker-Extraktion
# ---------------------------------------------------------------------------
def parse_tickers(df: pd.DataFrame) -> list[str]:
    """Extrahiere yfinance-Ticker aus dem Holdings-DataFrame."""
    log.info("DataFrame-Spalten: %s", list(df.columns))

    ticker_col   = next((c for c in df.columns if "ticker"   in c.lower()), None)
    exchange_col = next((c for c in df.columns if "exchange" in c.lower()), None)
    asset_col    = next((c for c in df.columns if "asset"    in c.lower()
                         and "class" in c.lower()), None)

    if not ticker_col or not exchange_col:
        log.error("Spalten 'Ticker'/'Exchange' nicht gefunden. Vorhanden: %s", list(df.columns))
        return []

    tickers: list[str] = []
    skipped = 0
    for _, row in df.iterrows():
        if asset_col:
            ac = str(row.get(asset_col, "")).strip().lower()
            if ac not in ("equity", "aktie", "stock"):
                skipped += 1
                continue
        raw = str(row[ticker_col]).strip()
        exch = str(row[exchange_col]).strip()
        t = build_yfinance_ticker(raw, exch)
        if t:
            tickers.append(t)

    log.info("%d Aktien-Ticker extrahiert (%d übersprungen).", len(tickers), skipped)
    return list(dict.fromkeys(tickers))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("=== 00_fetch_constituents.py — start ===")

    df = fetch_ishares_holdings()

    if df is None:
        log.error(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  iShares-Download fehlgeschlagen                             ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║  Mögliche Ursachen:                                          ║\n"
            "║   • Kein Internetzugang                                      ║\n"
            "║   • iShares blockiert diesen Server (IP-Whitelist)           ║\n"
            "║                                                              ║\n"
            "║  Lösung — CSV manuell herunterladen:                         ║\n"
            "║   1. Öffne: https://www.ishares.com/uk/individual/en/        ║\n"
            "║             products/251904/                                 ║\n"
            "║   2. Klicke 'Download Holdings' (CSV)                        ║\n"
            "║   3. Lade die Datei in der App hoch (STOXX 600 Bereich)      ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        sys.exit(1)

    tickers = parse_tickers(df)

    if len(tickers) < 100:
        log.warning("Nur %d Ticker — CSV-Format evtl. geändert.", len(tickers))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps({"tickers": tickers, "count": len(tickers)}, indent=2)
    )
    log.info("Gespeichert: %d Ticker → %s", len(tickers), OUTPUT_PATH)
    log.info("=== 00_fetch_constituents.py — done ===")


if __name__ == "__main__":
    main()
