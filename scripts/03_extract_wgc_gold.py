"""
Extract BRICS gold holdings (tonnes) from the World Gold Council quarterly export
and save them in the format of data/manual/gold_tonnes.csv.

Usage (from the project folder):
    python scripts/03_extract_wgc_gold.py data/raw/wgc/wgc_gold_reserves_quarterly.xlsx
"""

import sys
from datetime import date

import pandas as pd

from config import MANUAL, CLEAN

# WGC country name -> the name used everywhere else in the project (TIC files)
COUNTRY_MAP = {
    "China": "China",
    "Russian Federation": "Russia",
    "India": "India",
    "Brazil": "Brazil",
    "South Africa": "South Africa",
}
SOURCE = "World Gold Council - Gold reserves by country (based on IMF IFS)"


def quarter_to_date(label):
    """'Q4 18' -> Timestamp('2018-12-31'): the last day of that quarter."""
    q, yy = label.split()  # 'Q4', '18'
    period = pd.Period(f"20{yy}{q}", freq="Q")  # '2018Q4'
    return period.to_timestamp(how="end").normalize()


def main(path):
    # 1) Read only the 'Data' sheet (the first sheet is WGC's disclaimer).
    raw = pd.read_excel(path, sheet_name="Data")

    # 2) Keep the five BRICS founders and rename them to project names.
    brics = raw[raw["Country"].isin(COUNTRY_MAP)].copy()
    missing = set(COUNTRY_MAP) - set(brics["Country"])
    if missing:
        raise ValueError(f"Not found in WGC file: {missing} (check spelling)")
    brics["Country"] = brics["Country"].map(COUNTRY_MAP)

    # 3) Wide -> long: one row per country per quarter.
    long = brics.melt(id_vars="Country", var_name="quarter", value_name="tonnes")

    # 4) Clean values: 'AWAITED' or blanks become NaN instead of crashing.
    long["tonnes"] = pd.to_numeric(long["tonnes"], errors="coerce")
    n_bad = long["tonnes"].isna().sum()
    if n_bad:
        print(f"Warning: {n_bad} non-numeric values set to NaN")

    # 5) Quarter label -> quarter-end date, to line up with December TIC data.
    long["as_of_date"] = long["quarter"].map(quarter_to_date)

    # 6) Put in the template's column order and save.
    out = pd.DataFrame(
        {
            "country": long["Country"],
            "as_of_date": long["as_of_date"].dt.strftime("%Y-%m-%d"),
            "tonnes": long["tonnes"].round(2),
            "source": SOURCE,
            "page_or_table": "Quarterly export, " + long["quarter"],
            "retrieved": date.today().isoformat(),
        }
    ).sort_values(["country", "as_of_date"])
    out.to_csv(MANUAL / "gold_tonnes.csv", index=False)

    # 7) Extra convenience file: year-end (Q4) values in wide form for tables/charts.
    out["as_of_date"] = pd.to_datetime(out["as_of_date"])
    q4 = out[out["as_of_date"].dt.month == 12].copy()
    q4["year"] = q4["as_of_date"].dt.year
    year_end = q4.pivot(index="year", columns="country", values="tonnes")
    year_end.to_csv(CLEAN / "gold_yearend_tonnes.csv")

    # 8) Quick printout so you can eyeball it against the WGC chart.
    print(f"Saved {len(out)} rows -> {MANUAL / 'gold_tonnes.csv'}")
    print("\nYear-end gold holdings (tonnes):")
    print(year_end.round(1).to_string())
    first, last = year_end.iloc[0], year_end.iloc[-1]
    print("\nChange first -> last year (tonnes):")
    print((last - first).round(1).to_string())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/03_extract_wgc_gold.py <path to WGC xlsx>")
    main(sys.argv[1])
