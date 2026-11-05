"""
Shared settings for every script: folder paths, sample period and series codes.
Change things here once instead of editing every script.
"""
import os
from pathlib import Path

# Project root = the folder that contains /scripts. You can override it with an
# environment variable (useful for testing), e.g.  DEDOLLAR_ROOT=/some/path
ROOT = Path(os.environ.get("DEDOLLAR_ROOT", Path(__file__).resolve().parents[1]))

RAW_FRED = ROOT / "data" / "raw" / "fred"
RAW_MARKET = ROOT / "data" / "raw" / "market"
MANUAL = ROOT / "data" / "manual"
CLEAN = ROOT / "data" / "clean"
FIGURES = ROOT / "figures"
for p in (RAW_FRED, RAW_MARKET, MANUAL, CLEAN, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# Sample period. Dec 2017 is included so that January 2018 has a return / change.
START = "2017-12"
END = "2025-12"

# ---------------------------------------------------------------------------
# Treasury (TIC) series on FRED. Code = PREFIX + COUNTRY_ID
# ---------------------------------------------------------------------------
COUNTRIES = {
    "China": "41408",
    "Brazil": "30309",
    "India": "42102",
    "Russia": "16101",
    "Grand Total": "99996",       # all foreign holders, private + official
    "Foreign Official": "99990",  # central banks, governments, sovereign funds
}

TIC_MEASURES = {
    # headline holdings: long-term + short-term (bills), market value, USD millions
    "holdings_total": "FORTREASPOS",
    # long-term only (notes & bonds) -- used for the flow/valuation decomposition,
    # because the valuation series exists only for long-term securities
    "lt_holdings": "FORLTTREASPOS",
    "lt_net_transactions": "FORLTTREASNET",
    "lt_valuation_change": "FORLTTREASVALCHG",
}

# ---------------------------------------------------------------------------
# Macro / rates series on FRED (for RQ2 and the risk-free rate in RQ3)
# ---------------------------------------------------------------------------
MACRO = {
    "GS10": "10-year Treasury yield, monthly average, % p.a.",
    "DGS10": "10-year Treasury yield, daily, % p.a.",
    "FEDFUNDS": "Effective federal funds rate, monthly average, % p.a.",
    "T10YIE": "10-year breakeven inflation, daily, %",
    "THREEFYTP10": "10-year term premium (Kim-Wright model), daily, %",
    "TB3MS": "3-month Treasury bill, secondary market, monthly average, % p.a.",
}
DAILY_SERIES = {"DGS10", "T10YIE", "THREEFYTP10"}

# ---------------------------------------------------------------------------
# Market data (yfinance) for the RQ3 portfolio backtest
# ---------------------------------------------------------------------------
TICKERS = {
    "SPY": "US equities (S&P 500 ETF)",
    "AGG": "US aggregate bonds ETF",
    "IEF": "7-10 year Treasury ETF (robustness check)",
    "GLD": "Gold ETF",
}

# Reference values from the Treasury 'Major Foreign Holders' table (USD bn),
# used only to cross-check the FRED download.
MFH_CHECK = {
    ("China", "2018-12"): 1124.3,
    ("China", "2025-12"): 684.4,
    ("Brazil", "2018-12"): 303.1,
    ("Brazil", "2025-12"): 168.7,
    ("India", "2018-12"): 141.3,
    ("India", "2025-12"): 182.9,
    ("Grand Total", "2018-12"): 6270.1,
    ("Grand Total", "2025-12"): 9269.5,
}
