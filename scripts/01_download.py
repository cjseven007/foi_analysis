"""
Step 1: download every automatic data series and save it UNCHANGED to data/raw/.
Every download is logged (what, from where, when, how many rows) so the
report's Data Sources section and the lecturer's evidence trail are easy.

Run from the project folder:   python scripts/01_download.py
"""
import time
from datetime import datetime, timezone

import pandas as pd

from config import RAW_FRED, RAW_MARKET, ROOT, COUNTRIES, TIC_MEASURES, MACRO, TICKERS

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
log_rows = []


def log(source, series_id, url, status, df=None):
    """Remember one line for data/raw/download_log.csv."""
    log_rows.append({
        "source": source,
        "series_id": series_id,
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "rows": None if df is None else len(df),
        "first_date": None if df is None or df.empty else str(df.index.min().date()),
        "last_date": None if df is None or df.empty else str(df.index.max().date()),
    })


def download_fred(series_id):
    """Download one FRED series as a CSV and save it untouched."""
    url = FRED_CSV.format(series_id)
    try:
        # FRED's CSV has two columns: the date and the value. Missing values are ".".
        df = pd.read_csv(url, index_col=0, parse_dates=True, na_values=".")
        df.columns = [series_id]
        df.index.name = "date"
        df.to_csv(RAW_FRED / f"{series_id}.csv")
        log("FRED", series_id, url, "ok", df)
        print(f"  ok   {series_id:<22} {len(df):>5} rows")
    except Exception as e:  # a wrong code or network problem should not stop the rest
        log("FRED", series_id, url, f"FAILED: {e}")
        print(f"  FAIL {series_id:<22} {e}")
    time.sleep(0.5)  # be polite to the server


def main():
    print("Treasury (TIC) series from FRED:")
    for measure, prefix in TIC_MEASURES.items():
        for country, cid in COUNTRIES.items():
            download_fred(prefix + cid)

    print("\nMacro series from FRED:")
    for sid in MACRO:
        download_fred(sid)

    print("\nMarket prices from yfinance:")
    try:
        import yfinance as yf
        tickers = list(TICKERS)
        # interval='1mo' -> one row per month. auto_adjust=True -> prices are
        # adjusted for dividends/splits, so % changes are TOTAL returns.
        px = yf.download(tickers, start="2017-11-01", end="2026-01-01",
                         interval="1mo", auto_adjust=True, progress=False)["Close"]
        px = px[tickers]              # fixed column order
        px.columns.name = None        # avoid an extra header row in the CSV
        px.index.name = "date"
        px.to_csv(RAW_MARKET / "etf_prices_monthly.csv")
        log("yfinance", ",".join(tickers), "Yahoo Finance via yfinance", "ok", px)
        print(f"  ok   {len(px)} monthly rows for {tickers}")
    except Exception as e:
        log("yfinance", ",".join(TICKERS), "Yahoo Finance via yfinance", f"FAILED: {e}")
        print(f"  FAIL yfinance: {e}")

    pd.DataFrame(log_rows).to_csv(ROOT / "data" / "raw" / "download_log.csv", index=False)
    failed = [r["series_id"] for r in log_rows if r["status"] != "ok"]
    print(f"\nDone. Log saved to data/raw/download_log.csv. Failed: {failed or 'none'}")


if __name__ == "__main__":
    main()
