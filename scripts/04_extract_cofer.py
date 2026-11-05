"""
Extract the world currency composition of FX reserves from the IMF COFER download.

Outputs
  data/manual/cofer_usd_share.csv      -> template format (USD share + total reserves)
  data/clean/cofer_composition_q.csv   -> every currency's share, long format (for charts)

Usage (from the project folder):
    python scripts/04_extract_cofer.py data/raw/imf/cofer_download.csv
"""

import sys
from datetime import date

import pandas as pd

from config import MANUAL, CLEAN

FIRST_Q, LAST_Q = "2018-Q4", "2025-Q4"  # study window (2026 quarters are excluded)


def main(path):
    raw = pd.read_csv(path, low_memory=False)

    # 1) Keep: World aggregate, quarterly rows, allocated reserves.
    #    (The Advanced/Emerging split is blank for our period, so it is not used.)
    q = raw[
        (raw["COUNTRY"] == "World")
        & (raw["FREQUENCY"] == "Quarterly")
        & (raw["INDICATOR"] == "Allocated foreign exchange reserves")
    ].copy()

    # 2) Quarterly value columns look like '2018-Q4'. Annual columns ('2018') are dropped.
    qcols = [
        c
        for c in raw.columns
        if len(c) == 7 and c[4:6] == "-Q" and FIRST_Q <= c <= LAST_Q
    ]

    # 3) Short currency name: 'Claims in US dollar' -> 'US dollar'
    q["currency"] = q["FXR_CURRENCY"].str.replace("Claims in ", "", regex=False)

    # 4) Wide -> long: one row per currency x measure x quarter.
    long = q.melt(
        id_vars=["currency", "TYPE_OF_TRANSFORMATION"],
        value_vars=qcols,
        var_name="quarter",
        value_name="value",
    )
    long["value"] = pd.to_numeric(long["value"], errors="coerce")

    # 5) Split into shares (%) and nominal values (USD millions -> USD billions).
    shares = long[long["TYPE_OF_TRANSFORMATION"] == "Shares"].pivot(
        index="quarter", columns="currency", values="value"
    )
    nominal = (
        long[long["TYPE_OF_TRANSFORMATION"] == "Nominal value"].pivot(
            index="quarter", columns="currency", values="value"
        )
    ) / 1000

    # 6) Checks: shares should add to ~100% (excluding the 'All currencies' total row).
    parts = shares.drop(columns="All currencies", errors="ignore")
    off = (parts.sum(axis=1) - 100).abs()
    if (off > 0.5).any():
        print(
            "Warning: currency shares do not add to 100% in:",
            off[off > 0.5].round(2).to_dict(),
        )

    # Recompute the USD share from nominal values as a cross-check of the published share.
    usd_check = nominal["US dollar"] / nominal["All currencies"] * 100
    gap = (usd_check - shares["US dollar"]).abs().max()
    print(f"USD share: published vs recomputed from USD values, max gap = {gap:.4f} pp")

    # 7) Template file for data/manual/
    vintage = raw["PUBLICATION_DATE"].dropna().iloc[0][:10]
    out = pd.DataFrame(
        {
            "quarter": shares.index.str.replace("-", ""),  # '2018-Q4' -> '2018Q4'
            "usd_share_pct": shares["US dollar"].round(2).values,
            "total_fx_reserves_usd_bn": nominal["All currencies"].round(1).values,
            "source": f"IMF COFER (World, allocated reserves), release {vintage}",
            "retrieved": date.today().isoformat(),
        }
    )
    out.to_csv(MANUAL / "cofer_usd_share.csv", index=False)

    # 8) Full composition (long) for a stacked area / bar chart.
    comp = parts.reset_index().melt(
        id_vars="quarter", var_name="currency", value_name="share_pct"
    )
    comp["date"] = (
        pd.PeriodIndex(comp["quarter"].str.replace("-", ""), freq="Q")
        .to_timestamp(how="end")
        .normalize()
    )
    comp.to_csv(CLEAN / "cofer_composition_q.csv", index=False)

    # 9) Printout to eyeball
    print(f"Data vintage (IMF publication date): {vintage}")
    print(f"Saved {len(out)} quarters -> {MANUAL / 'cofer_usd_share.csv'}")
    print("\nQ4 values:")
    q4 = out[out["quarter"].str.endswith("Q4")].set_index("quarter")
    print(q4[["usd_share_pct", "total_fx_reserves_usd_bn"]].to_string())
    print("\nShares (%), first vs last quarter:")
    print(
        parts.loc[[FIRST_Q, LAST_Q]]
        .T.round(2)
        .sort_values(LAST_Q, ascending=False)
        .to_string()
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/04_extract_cofer.py <path to COFER csv>")
    main(sys.argv[1])
