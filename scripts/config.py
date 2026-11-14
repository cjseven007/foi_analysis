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
TABLES = ROOT / "tables"
for p in (RAW_FRED, RAW_MARKET, MANUAL, CLEAN, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# Sample period. Dec 2017 is included so that January 2018 has a return / change.
RQ1_START = "2017-12"  # Treasury holdings, gold, COFER (frozen)
RQ3_START = "2004-12"  # portfolio backtest: longer sample for robustness
START = RQ1_START  # kept so older code still works
END = "2025-12"

# ---------------------------------------------------------------------------
# Treasury (TIC) series on FRED. Code = PREFIX + COUNTRY_ID
# ---------------------------------------------------------------------------
COUNTRIES = {
    "China": "41408",
    "Brazil": "30309",
    "India": "42102",
    "Russia": "16101",
    "Grand Total": "99996",  # all foreign holders, private + official
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
    "DTWEXBGS": "Nominal broad U.S. dollar index, daily",
    "DEXMAUS": "Malaysian ringgit per U.S. dollar, daily",
    "CPIAUCSL": "U.S. CPI, all urban consumers, monthly",
}
DAILY_SERIES = {"DGS10", "T10YIE", "THREEFYTP10", "DTWEXBGS", "DEXMAUS"}

# ---------------------------------------------------------------------------
# Market data (yfinance) for the RQ3 portfolio backtest
# ---------------------------------------------------------------------------
TICKERS = {
    "SPY": "US equities (S&P 500 ETF)",
    "AGG": "US aggregate bonds ETF",
    "IEF": "7-10 year Treasury ETF (robustness check)",
    "GLD": "Gold ETF",
    "EFA": "International developed equities ETF",
    "EEM": "Emerging market equities ETF",
    "BWX": "International government bonds ETF (unhedged)",
    "FXF": "Swiss franc ETF",
    "FXY": "Japanese yen ETF",
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

# ---------------------------------------------------------------------------
# RQ3 Specific Directories, Windows & Portfolio Definitions
# ---------------------------------------------------------------------------
FIG_RQ3 = FIGURES / "fig_rq3"
TABLES_RQ3 = TABLES / "table_rq3"
for p in (FIG_RQ3, TABLES_RQ3):
    p.mkdir(parents=True, exist_ok=True)

# Key RQ3 analytical windows
RQ3_MULTI_START = (
    "2008-01"  # Earliest full year where all 9 ETFs (incl. BWX, FXY, FXF) exist
)
RQ3_MAIN_START = "2018-01"  # Primary BRICS de-dollarization window matching RQ1 & RQ2
FREEZE_DATE = "2022-02"  # G7 freeze of Russian central bank reserves

RQ3_PORTFOLIOS = {
    "P1: Pure USD 60/40 (60% SPY / 40% AGG)": {"SPY": 0.60, "AGG": 0.40},
    "P1b: Treasury 60/40 (60% SPY / 40% IEF)": {"SPY": 0.60, "IEF": 0.40},
    "P2: Moderate Gold (60% SPY / 30% AGG / 10% GLD)": {
        "SPY": 0.60,
        "AGG": 0.30,
        "GLD": 0.10,
    },
    "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)": {
        "SPY": 0.60,
        "AGG": 0.20,
        "GLD": 0.20,
    },
    "P4: Currency Safe-Haven (60% SPY / 20% AGG / 10% FXF / 10% FXY)": {
        "SPY": 0.60,
        "AGG": 0.20,
        "FXF": 0.10,
        "FXY": 0.10,
    },
    "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)": {
        "SPY": 0.60,
        "AGG": 0.20,
        "BWX": 0.20,
    },
    "P6: Global De-dollarized (40% SPY / 10% EFA / 10% EEM / 15% AGG / 10% BWX / 15% GLD)": {
        "SPY": 0.40,
        "EFA": 0.10,
        "EEM": 0.10,
        "AGG": 0.15,
        "BWX": 0.10,
        "GLD": 0.15,
    },
    "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)": {
        "SPY": 1 / 3,
        "AGG": 1 / 3,
        "GLD": 1 / 3,
    },
}
