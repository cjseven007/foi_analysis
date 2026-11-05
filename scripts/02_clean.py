"""
Step 2: turn the raw files into tidy, aligned, analysis-ready CSVs in data/clean/,
then run validation checks. Never edits anything in data/raw/.

Run from the project folder:   python scripts/02_clean.py
"""
import numpy as np
import pandas as pd

from config import (RAW_FRED, RAW_MARKET, MANUAL, CLEAN, START, END,
                    COUNTRIES, TIC_MEASURES, MACRO, DAILY_SERIES, TICKERS, MFH_CHECK)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_raw_fred(series_id):
    """Read one saved FRED file. Returns a Series, or None if it was not downloaded."""
    path = RAW_FRED / f"{series_id}.csv"
    if not path.exists():
        print(f"  missing raw file: {series_id} (skipped)")
        return None
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    return pd.to_numeric(s, errors="coerce")  # anything non-numeric -> NaN


def to_month(s, daily=False):
    """
    Put any series on ONE common monthly index (pandas Period 'M', e.g. 2025-12).

    - FRED monthly data are stamped on the 1st of the month (2025-12-01) but mean
      'December 2025'. yfinance monthly bars are also stamped on the 1st.
      Converting both to Period('2025-12') removes the 1st-vs-31st problem.
    - Daily series (e.g. DGS10) are first reduced to the LAST available value in
      each month (a month-end snapshot), so they match end-of-month holdings.
    """
    if daily:
        s = s.dropna().resample("ME").last()
    s.index = s.index.to_period("M")
    return s


def window(df):
    """Keep only the study period."""
    return df.loc[START:END]


def safe_pct_change(new, old, min_base=1.0):
    """
    % change that refuses to divide by a tiny base. Russia's holdings fell to
    ~$0.03bn, so any % change from there is meaningless. Returns NaN instead.
    """
    return np.where(np.abs(old) >= min_base, (new / old - 1) * 100, np.nan)


# ---------------------------------------------------------------------------
# 1) Treasury holdings, flows and valuation
# ---------------------------------------------------------------------------
def clean_tic():
    print("Cleaning Treasury (TIC) series...")
    long_rows = []
    for measure, prefix in TIC_MEASURES.items():
        for country, cid in COUNTRIES.items():
            s = read_raw_fred(prefix + cid)
            if s is None:
                continue
            s = window(to_month(s)) / 1000  # USD millions -> USD billions
            long_rows.append(pd.DataFrame({
                "date": s.index, "country": country, "measure": measure, "usd_bn": s.values,
            }))
    tidy = pd.concat(long_rows, ignore_index=True)

    # Tidy ("long") format: one row per date x country x measure. Easiest for seaborn.
    tidy.to_csv(CLEAN / "tic_long.csv", index=False)

    # Wide headline table: rows = months, columns = countries. Easiest for tables.
    holdings = (tidy[tidy.measure == "holdings_total"]
                .pivot(index="date", columns="country", values="usd_bn"))
    holdings = holdings[[c for c in COUNTRIES if c in holdings.columns]]
    holdings.to_csv(CLEAN / "holdings_monthly_bn.csv")

    # Year-end snapshot (December values only) for the report tables.
    year_end = holdings[holdings.index.month == 12].copy()
    year_end.index = year_end.index.year
    year_end.index.name = "year"
    year_end.to_csv(CLEAN / "holdings_yearend_bn.csv")

    # Decomposition table (long-term securities only):
    #   change in holdings  vs  net transactions + valuation change
    lt = (tidy[tidy.measure.str.startswith("lt_")]
          .pivot_table(index=["country", "date"], columns="measure", values="usd_bn")
          .reset_index())
    if {"lt_holdings", "lt_net_transactions", "lt_valuation_change"} <= set(lt.columns):
        lt = lt.sort_values(["country", "date"])
        lt["lt_change"] = lt.groupby("country")["lt_holdings"].diff()
        # whatever is not explained by trading or price moves (redemptions, reclassification, rounding)
        lt["other_residual"] = lt["lt_change"] - lt["lt_net_transactions"] - lt["lt_valuation_change"]
        lt.to_csv(CLEAN / "lt_decomposition_monthly_bn.csv", index=False)
    return holdings, year_end, lt


# ---------------------------------------------------------------------------
# 2) Macro / rates
# ---------------------------------------------------------------------------
def clean_macro():
    print("Cleaning macro series...")
    cols = {}
    for sid in MACRO:
        s = read_raw_fred(sid)
        if s is not None:
            cols[sid] = window(to_month(s, daily=sid in DAILY_SERIES))
    macro = pd.DataFrame(cols)
    macro.index.name = "date"
    # Rename daily-derived series so nobody mistakes them for monthly averages.
    macro = macro.rename(columns={c: f"{c}_monthend" for c in macro.columns if c in DAILY_SERIES})
    macro.to_csv(CLEAN / "macro_monthly.csv")
    return macro


# ---------------------------------------------------------------------------
# 3) Market returns for the portfolio backtest
# ---------------------------------------------------------------------------
def clean_market(macro):
    print("Cleaning market prices -> returns...")
    path = RAW_MARKET / "etf_prices_monthly.csv"
    if not path.exists():
        print("  missing etf_prices_monthly.csv (skipped)")
        return None
    px = pd.read_csv(path, index_col=0, parse_dates=True)
    px.index = px.index.to_period("M")
    px = px.loc[START:END]

    # Simple monthly return: r_t = P_t / P_{t-1} - 1. Adjusted prices -> total return.
    rets = px.pct_change().iloc[1:]  # first row has no previous month -> dropped

    # Risk-free rate: TB3MS is an ANNUAL % rate. Convert to a MONTHLY decimal return:
    #   (1 + annual)^(1/12) - 1
    # Use LAST month's rate (shift(1)): the rate you could lock in at the START of the month.
    if "TB3MS" in macro.columns:
        rf_monthly = (1 + macro["TB3MS"] / 100) ** (1 / 12) - 1
        rets["RF"] = rf_monthly.shift(1).reindex(rets.index)

    rets.index.name = "date"
    rets.to_csv(CLEAN / "returns_monthly.csv")
    return rets


# ---------------------------------------------------------------------------
# 4) Manual (hand-entered) files
# ---------------------------------------------------------------------------
MANUAL_SPECS = {
    "gold_tonnes.csv": ["country", "as_of_date", "tonnes", "source", "page_or_table", "retrieved"],
    "fx_reserves.csv": ["country", "as_of_date", "usd_bn", "source", "page_or_table", "retrieved"],
    "russia_currency_shares.csv": ["as_of_date", "currency", "share_pct", "source", "page_or_table"],
    "india_rbi.csv": ["as_of_date", "gold_tonnes", "gold_domestic_tonnes", "gold_share_pct",
                      "total_reserves_usd_bn", "source", "page_or_table"],
    "cofer_usd_share.csv": ["quarter", "usd_share_pct", "total_fx_reserves_usd_bn",
                            "source", "retrieved"],
}


def clean_manual():
    print("Checking manual files...")
    for fname, cols in MANUAL_SPECS.items():
        path = MANUAL / fname
        if not path.exists():
            print(f"  {fname}: not found")
            continue
        # comment='#' lets the template keep example lines that are ignored
        df = pd.read_csv(path, comment="#", skipinitialspace=True)
        missing = set(cols) - set(df.columns)
        if missing:
            print(f"  {fname}: MISSING COLUMNS {missing}")
            continue
        if df.empty:
            print(f"  {fname}: empty (fill it in by hand)")
            continue
        for c in df.columns:  # numbers stored as text -> numbers
            if c not in ("country", "currency", "source", "page_or_table", "retrieved", "quarter", "as_of_date"):
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "as_of_date" in df.columns:
            df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
            bad = df["as_of_date"].isna().sum()
            if bad:
                print(f"  {fname}: {bad} unreadable dates -- use YYYY-MM-DD")
        if not df["source"].notna().all():
            print(f"  {fname}: some rows have no source -- every number needs one")
        df.to_csv(CLEAN / f"manual_{fname}", index=False)
        print(f"  {fname}: {len(df)} rows ok")

    # Specific sanity check: Russia's shares for each date should add up to ~100%
    path = CLEAN / "manual_russia_currency_shares.csv"
    if path.exists():
        r = pd.read_csv(path)
        sums = r.groupby("as_of_date")["share_pct"].sum()
        off = sums[(sums - 100).abs() > 1.5]
        if len(off):
            print(f"  russia shares do not sum to ~100% on: {off.round(1).to_dict()}")


# ---------------------------------------------------------------------------
# 5) Validation report
# ---------------------------------------------------------------------------
def validate(holdings, year_end, lt, rets):
    print("\n================ VALIDATION ================")
    lines = []

    # (a) Coverage: are there gaps inside the sample period?
    expected = pd.period_range(START, END, freq="M")
    for c in holdings.columns:
        n_missing = holdings[c].reindex(expected).isna().sum()
        lines.append(f"Coverage {c:<17}: {len(expected) - n_missing}/{len(expected)} months")

    # (b) FRED vs Treasury 'Major Foreign Holders' table
    lines.append("\nFRED vs Major Foreign Holders table (USD bn):")
    for (country, month), ref in MFH_CHECK.items():
        p = pd.Period(month, "M")
        if country in holdings.columns and p in holdings.index:
            val = holdings.loc[p, country]
            lines.append(f"  {country:<12} {month}: FRED {val:8.1f} | MFH {ref:8.1f} | gap {val/ref*100-100:+5.1f}%")

    # (c) Decomposition identity: is the residual small?
    if lt is not None and "other_residual" in lt.columns:
        lines.append("\nDecomposition residual (change - net transactions - valuation), USD bn:")
        for c, g in lt.dropna(subset=["other_residual"]).groupby("country"):
            lines.append(f"  {c:<17} mean abs residual {g.other_residual.abs().mean():6.2f} | "
                         f"mean abs change {g.lt_change.abs().mean():6.2f}")

    # (d) Returns: obviously wrong values usually mean a units or date bug
    if rets is not None:
        lines.append("\nReturns check (monthly):")
        for c in rets.columns:
            r = rets[c].dropna()
            flag = "  <-- CHECK" if (r.abs() > 0.30).any() else ""
            lines.append(f"  {c:<4} n={len(r):3d}  mean {r.mean()*100:5.2f}%  "
                         f"min {r.min()*100:6.2f}%  max {r.max()*100:6.2f}%{flag}")

    # (e) Russia note
    if "Russia" in year_end.columns:
        lines.append(f"\nRussia year-end holdings (bn): {year_end['Russia'].round(2).to_dict()}")
        lines.append("  -> use absolute change, not % change, once below ~$1bn (see safe_pct_change)")

    report = "\n".join(lines)
    print(report)
    (CLEAN / "validation_report.txt").write_text(report)


def main():
    holdings, year_end, lt = clean_tic()
    macro = clean_macro()
    rets = clean_market(macro)
    clean_manual()
    validate(holdings, year_end, lt, rets)
    print(f"\nClean files written to {CLEAN}")


if __name__ == "__main__":
    main()
