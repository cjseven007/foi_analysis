"""
RQ1 figures: Treasury holdings, flow-vs-valuation, gold, COFER, Russia, India.
Reads only data/clean/ and data/manual/, writes PNGs (300 dpi) to figures/.

Run from the project folder:   python scripts/05_plot_rq1.py
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.transforms import offset_copy
import pandas as pd
import seaborn as sns

from config import CLEAN, MANUAL, FIGURES

# ---------------------------------------------------------------------------
# 1) Style: one look for every figure
# ---------------------------------------------------------------------------
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"  # text colours
GRID, AXIS = "#e1e0d9", "#c3c2b7"  # hairline grid, baseline

# Colour follows the ENTITY, not the chart: China is blue in every figure, etc.
COUNTRY = {
    "China": "#2a78d6",
    "Brazil": "#eb6834",
    "India": "#1baf7a",
    "Russia": "#eda100",
    "South Africa": "#e87ba4",
}
CURRENCY = {
    "US dollar": "#2a78d6",
    "Euro": "#eb6834",
    "Chinese yuan renminbi": "#1baf7a",
    "Japanese yen": "#eda100",
    "Pound sterling": "#e87ba4",
    "Gold": "#008300",
    "Other": "#a8a7a1",
}
FLOW = {"Net transactions": "#6250d6", "Valuation change": "#e34948"}
UP, DOWN = "#2a78d6", "#e34948"  # diverging pair (gain / loss)

# Event markers used on time charts (date, short label)
EVENTS = [
    ("2018-04-06", "US sanctions\non Russia"),
    ("2022-02-28", "Russian reserves\nfrozen"),
]

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update(
    {
        "font.family": ["Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2,
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.grid.axis": "y",
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 2,
        "lines.solid_capstyle": "round",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def finish(fig, name, title, subtitle, source, note=None):
    """Title block on top, source note at the bottom, save as 300-dpi PNG."""
    # Place text a fixed number of POINTS above/below the figure edge, so the
    # spacing is identical whatever the figure height.
    above = lambda pts: offset_copy(fig.transFigure, fig=fig, y=pts, units="points")
    fig.text(
        0.01,
        1.0,
        subtitle,
        transform=above(6),
        ha="left",
        va="bottom",
        fontsize=9,
        color=INK2,
    )
    fig.text(
        0.01,
        1.0,
        title,
        transform=above(20),
        ha="left",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    foot = f"Source: {source}" + (f"\nNote: {note}" if note else "")
    fig.text(
        0.01,
        0.0,
        foot,
        transform=above(-14),
        ha="left",
        va="top",
        fontsize=7,
        color=MUTED,
    )
    out = FIGURES / f"{name}.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out.name}")


def mark_events(ax, y_text=0.97):
    """Thin dashed vertical lines for the two key sanctions events."""
    for d, label in EVENTS:
        x = pd.Timestamp(d)
        ax.axvline(x, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
        ax.annotate(
            label,
            xy=(mdates.date2num(x), y_text),
            xycoords=ax.get_xaxis_transform(),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="top",
            fontsize=7,
            color=MUTED,
        )


def label_line_ends(ax, df, fmt="{:,.0f}"):
    """
    Write 'Name  value' just right of each line's last point (direct labels).
    Labels are placed bottom-up and pushed apart if they would overlap.
    Call AFTER setting the y-limits.
    """
    last = df.ffill().iloc[-1].sort_values()
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * 0.06  # minimum vertical distance between labels
    x_end = df.index[-1]
    x_text = x_end + pd.Timedelta(days=45)
    placed = []
    for name, y in last.items():
        y_text = max(y, placed[-1] + gap) if placed else y
        placed.append(y_text)
        value = (
            f"{y:,.2f}" if abs(y) < 1 else fmt.format(y)
        )  # tiny values: show 0.03, not 0
        ax.annotate(
            f"{name}  {value}",
            xy=(x_end, y),
            xytext=(x_text, y_text),
            textcoords="data",
            va="center",
            fontsize=8,
            color=INK,
            annotation_clip=False,
            arrowprops=(
                dict(arrowstyle="-", color=AXIS, lw=0.6) if y_text != y else None
            ),
        )


def month_index(df):
    """'2018-01' strings -> month-end Timestamps for matplotlib."""
    df.index = pd.PeriodIndex(df.index, freq="M").to_timestamp(how="end").normalize()
    return df


def year_axis(ax):
    """One tick per January, 2018-2025, and no empty space after Dec 2025."""
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2018, 2026)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(pd.Timestamp("2017-12-15"), pd.Timestamp("2026-01-15"))


# ---------------------------------------------------------------------------
# 2) Load clean data
# ---------------------------------------------------------------------------
H = month_index(pd.read_csv(CLEAN / "holdings_monthly_bn.csv", index_col=0))
H = H.loc["2018-01":]  # Dec 2017 is only needed for changes
BRICS = [c for c in ["China", "Brazil", "India", "Russia"] if c in H]


# ---------------------------------------------------------------------------
# 3) Figures
# ---------------------------------------------------------------------------
def fig_holdings_levels():
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for c in BRICS:
        ax.plot(H.index, H[c], color=COUNTRY[c], label=c)
    ax.set_ylim(0, H[BRICS].max().max() * 1.1)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}bn"))
    year_axis(ax)
    mark_events(ax)
    label_line_ends(ax, H[BRICS])
    ax.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.08))
    finish(
        fig,
        "fig_rq1_01_holdings_levels",
        "BRICS Treasury holdings fell unevenly",
        "U.S. Treasury securities held, end of month, Jan 2018 – Dec 2025 (USD billions)",
        "U.S. Treasury TIC via FRED (FORTREASPOS series).",
        "Country attribution is by custodian location; values include private holders and are at market value.",
    )


def fig_holdings_indexed():
    base = H.loc["2018-01"].iloc[0]
    cols = [c for c in ["China", "Brazil", "India"] if c in H] + ["Grand Total"]
    idx = H[cols] / base[cols] * 100
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for c in cols:
        style = (
            dict(color=MUTED, ls=(0, (4, 2)), lw=1.6)
            if c == "Grand Total"
            else dict(color=COUNTRY[c])
        )
        ax.plot(
            idx.index,
            idx[c],
            label="All foreign holders" if c == "Grand Total" else c,
            **style,
        )
    ax.axhline(100, color=AXIS, lw=0.8)
    year_axis(ax)
    mark_events(ax)
    label_line_ends(
        ax, idx.rename(columns={"Grand Total": "All foreign"}), fmt="{:.0f}"
    )
    ax.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.08))
    finish(
        fig,
        "fig_rq1_02_holdings_indexed",
        "Others kept buying while China and Brazil cut back",
        "Treasury holdings indexed to January 2018 = 100",
        "Author calculations from U.S. Treasury TIC via FRED.",
        "Russia is omitted: its holdings fell to near zero, so an index is not meaningful.",
    )


def fig_share_of_foreign():
    share = H[BRICS].div(H["Grand Total"], axis=0) * 100
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    # stacked area: the top edge is the combined BRICS-4 share
    ax.stackplot(
        share.index,
        *[share[c] for c in BRICS],
        colors=[COUNTRY[c] for c in BRICS],
        labels=BRICS,
        edgecolor="white",
        linewidth=0.8,
        alpha=0.95,
    )
    tot = share.sum(axis=1)
    for d in [tot.index[0], tot.index[-1]]:
        ax.annotate(
            f"{tot[d]:.1f}%",
            xy=(d, tot[d]),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=INK,
        )
    ax.set_ylim(0, tot.max() * 1.2)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    year_axis(ax)
    mark_events(ax)
    ax.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.08))
    finish(
        fig,
        "fig_rq1_03_share_of_foreign",
        "The BRICS share of foreign-held Treasuries more than halved",
        "Share of all foreign holdings of U.S. Treasury securities (%), stacked",
        "Author calculations from U.S. Treasury TIC via FRED (FORTREASPOS99996 as denominator).",
    )


def fig_decomposition():
    d = pd.read_csv(CLEAN / "lt_decomposition_monthly_bn.csv")
    d["year"] = pd.PeriodIndex(d["date"], freq="M").year
    d = d[(d["year"] >= 2018) & (d["year"] <= 2025)]
    ann = (
        d.groupby(["country", "year"])[["lt_net_transactions", "lt_valuation_change"]]
        .sum()
        .rename(
            columns={
                "lt_net_transactions": "Net transactions",
                "lt_valuation_change": "Valuation change",
            }
        )
    )
    countries = [
        c for c in ["China", "Brazil", "India"] if c in ann.index.get_level_values(0)
    ]
    fig, axes = plt.subplots(1, len(countries), figsize=(9, 3.4), sharey=False)
    for ax, c in zip(axes, countries):
        a = ann.loc[c]
        x = range(len(a))
        w = 0.4
        for k, (col, off) in enumerate(
            [("Net transactions", -w / 2), ("Valuation change", w / 2)]
        ):
            ax.bar(
                [i + off for i in x],
                a[col],
                width=w - 0.04,
                color=FLOW[col],
                label=col if c == countries[0] else None,
            )
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(list(x), [str(y) for y in a.index], fontsize=7)
        ax.set_title(c, loc="left", fontsize=10, fontweight="bold")
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    axes[0].set_ylabel("USD billions")
    fig.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout()
    finish(
        fig,
        "fig_rq1_04_flow_vs_valuation",
        "Most of China’s decline was real selling, not price effects",
        "Annual net purchases (+) / sales (−) vs price-driven valuation change, long-term Treasuries, 2018–2025",
        "U.S. Treasury TIC via FRED (FORLTTREASNET, FORLTTREASVALCHG series).",
        "Each panel has its own scale. Long-term securities only (notes and bonds); bills are excluded.",
    )


def fig_gold():
    g = pd.read_csv(MANUAL / "gold_tonnes.csv", parse_dates=["as_of_date"])
    g = g.pivot(index="as_of_date", columns="country", values="tonnes")
    order = [
        c for c in ["China", "Russia", "India", "Brazil", "South Africa"] if c in g
    ]
    fig, axes = plt.subplots(1, len(order), figsize=(10, 2.8), sharey=False)
    for ax, c in zip(axes, order):
        s = g[c]
        ax.plot(s.index, s, color=COUNTRY[c])
        ax.set_ylim(0, s.max() * 1.3)
        chg = s.iloc[-1] - s.iloc[0]
        ax.set_title(c, loc="left", fontsize=10, fontweight="bold")
        ax.text(
            0,
            1.0,
            f"{s.iloc[0]:,.0f} → {s.iloc[-1]:,.0f} t  ({chg:+,.0f} t)",
            transform=offset_copy(ax.transAxes, fig=fig, y=-2, units="points"),
            va="top",
            fontsize=7.5,
            color=INK2,
        )
        ax.axvline(
            pd.Timestamp("2022-02-28"), ymax=0.82, color=MUTED, lw=0.8, ls=(0, (3, 3))
        )
        ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in (2019, 2021, 2023, 2025)])
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    axes[0].set_ylabel("Tonnes")
    fig.tight_layout()
    finish(
        fig,
        "fig_rq1_05_gold_tonnes",
        "Gold accumulation: large, but not uniform",
        "Official gold holdings, quarterly, Q4 2018 – Q4 2025 (tonnes). Dashed line: Feb 2022 reserve freeze",
        "World Gold Council, Gold reserves by country (based on IMF IFS).",
        "Each panel has its own scale. Tonnes measure physical holdings and are unaffected by the gold price.",
    )


def fig_cofer_change():
    comp = pd.read_csv(CLEAN / "cofer_composition_q.csv", parse_dates=["date"])
    w = comp.pivot(index="date", columns="currency", values="share_pct")
    delta = (w.iloc[-1] - w.iloc[0]).sort_values()
    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = [DOWN if v < 0 else UP for v in delta]
    ax.barh(delta.index.str.replace(" renminbi", ""), delta, color=colors, height=0.6)
    ax.axvline(0, color=INK2, lw=0.8)
    for i, v in enumerate(delta):
        ax.text(
            v + (0.08 if v >= 0 else -0.08),
            i,
            f"{v:+.2f} pp",
            va="center",
            ha="left" if v >= 0 else "right",
            fontsize=8,
            color=INK,
        )
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter("{x:+.0f} pp"))
    lo, hi = delta.min(), delta.max()
    ax.set_xlim(lo - 1.4, hi + 1.4)
    finish(
        fig,
        "fig_rq1_06_cofer_change",
        "The dollar's lost share went to 'other' currencies, not the yuan",
        f"Change in share of world FX reserves, {w.index[0]:%Y} Q4 to {w.index[-1]:%Y} Q4 (percentage points)",
        "IMF COFER (world, allocated reserves), 30 Sep 2026 release; author calculations.",
        "'Other currencies' is the IMF residual for currencies not listed separately. Gold is not part of COFER.",
    )


def fig_cofer_usd():
    c = pd.read_csv(MANUAL / "cofer_usd_share.csv", comment="#")
    c["date"] = (
        pd.PeriodIndex(c["quarter"], freq="Q").to_timestamp(how="end").normalize()
    )
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    ax.plot(
        c["date"],
        c["usd_share_pct"],
        color=CURRENCY["US dollar"],
        marker="o",
        markersize=3,
    )
    for i in [0, len(c) - 1]:
        ax.annotate(
            f"{c['usd_share_pct'].iloc[i]:.2f}%",
            xy=(c["date"].iloc[i], c["usd_share_pct"].iloc[i]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=INK,
        )
    ax.set_ylim(50, 65)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    year_axis(ax)
    ax.set_xlim(
        pd.Timestamp("2018-10-01"), pd.Timestamp("2026-01-15")
    )  # data starts Q4 2018
    mark_events(ax)
    finish(
        fig,
        "fig_rq1_07_cofer_usd_share",
        "The dollar is still the main reserve currency, but its share is slipping",
        "U.S. dollar share of world allocated FX reserves, quarterly, Q4 2018 – Q4 2025 (%). Axis starts at 50%",
        "IMF COFER (world, allocated reserves), 30 Sep 2026 release.",
        "Shares are valued at end-quarter exchange rates, so a weaker dollar lowers the share without any selling.",
    )


def fig_russia():
    r = pd.read_csv(
        MANUAL / "russia_currency_shares.csv", comment="#", parse_dates=["as_of_date"]
    )
    names = {
        "USD": "US dollar",
        "EUR": "Euro",
        "CNY": "Chinese yuan renminbi",
        "GBP": "Pound sterling",
        "Gold": "Gold",
        "Other": "Other",
    }
    r["currency"] = r["currency"].map(names)
    w = r.pivot(index="as_of_date", columns="currency", values="share_pct")
    order = [
        c
        for c in [
            "US dollar",
            "Euro",
            "Chinese yuan renminbi",
            "Pound sterling",
            "Gold",
            "Other",
        ]
        if c in w
    ]
    w = w[order]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    labels = [f"End-{d:%Y}" for d in w.index]
    bottom = pd.Series(0.0, index=w.index)
    for c in order:
        ax.bar(
            labels,
            w[c],
            bottom=bottom,
            color=CURRENCY[c],
            width=0.6,
            edgecolor="white",
            linewidth=1.5,
            label=c.replace(" renminbi", ""),
        )
        for i, (v, b) in enumerate(zip(w[c], bottom)):
            if v >= 5:  # print the value only where it fits
                ax.text(
                    i,
                    b + v / 2,
                    f"{v:.1f}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="#0b0b0b" if c in ("Japanese yen", "Other") else "white",
                )
        bottom += w[c]
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    finish(
        fig,
        "fig_rq1_08_russia_composition",
        "Russia had largely left the dollar before the 2022 freeze",
        "Bank of Russia foreign currency and gold assets by currency (% of market value)",
        "Bank of Russia Annual Reports 2018 and 2021, Chart 32.",
        "Shares include gold in the total, unlike IMF COFER. Values below 5% are not printed.",
    )


def fig_india():
    d = pd.read_csv(CLEAN / "manual_india_rbi.csv", parse_dates=["as_of_date"])
    d["abroad"] = d["gold_tonnes"] - d["gold_domestic_tonnes"]
    labels = [f"{x:%b %Y}" for x in d["as_of_date"]]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(
        labels,
        d["gold_domestic_tonnes"],
        color=COUNTRY["India"],
        width=0.55,
        edgecolor="white",
        linewidth=1.5,
        label="Held in India",
    )
    ax.bar(
        labels,
        d["abroad"],
        bottom=d["gold_domestic_tonnes"],
        color="#a8a7a1",
        width=0.55,
        edgecolor="white",
        linewidth=1.5,
        label="Held abroad (BoE / BIS) and gold deposits",
    )
    for i, row in d.iterrows():
        pct = row["gold_domestic_tonnes"] / row["gold_tonnes"] * 100
        ax.text(
            i,
            row["gold_domestic_tonnes"] / 2,
            f"{row['gold_domestic_tonnes']:,.0f} t\n({pct:.0f}%)",
            ha="center",
            va="center",
            fontsize=8,
            color="white",
        )
        ax.text(
            i,
            row["gold_tonnes"] + 15,
            f"Total {row['gold_tonnes']:,.0f} t",
            ha="center",
            fontsize=8,
            color=INK,
        )
    ax.set_ylim(0, d["gold_tonnes"].max() * 1.15)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    finish(
        fig,
        "fig_rq1_09_india_gold_location",
        "India bought gold and brought it home",
        "Reserve Bank of India gold holdings by location (tonnes)",
        "RBI Half Yearly Reports on Management of Foreign Exchange Reserves (Mar 2019; Sep 2025), Sec. I.6.",
        "Mar 2019 domestic figure derived as total minus gold held overseas.",
    )


if __name__ == "__main__":
    print("Drawing RQ1 figures...")
    for f in [
        fig_holdings_levels,
        fig_holdings_indexed,
        fig_share_of_foreign,
        fig_decomposition,
        fig_gold,
        fig_cofer_change,
        fig_cofer_usd,
        fig_russia,
        fig_india,
    ]:
        try:
            f()
        except FileNotFoundError as e:
            print(f"  skipped {f.__name__}: missing {e.filename}")
    print(f"Done -> {FIGURES}")
