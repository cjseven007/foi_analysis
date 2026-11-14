"""
RQ3 & Objective 3 Analysis and Visualization Pipeline
Reads data/clean/returns_monthly.csv and data/clean/macro_monthly.csv.
Saves 300-DPI PNG figures to figures/fig_rq3/ and summary CSV tables to tables/table_rq3/.

Run from the project root folder:
    python scripts/rq3/run_rq3_analysis.py
"""

import sys
from pathlib import Path

# Allow importing config.py from the parent scripts/ directory
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.transforms import offset_copy
from scipy.optimize import minimize
import seaborn as sns

from config import (
    CLEAN,
    FIG_RQ3,
    TABLES_RQ3,
    RQ3_MULTI_START,
    RQ3_MAIN_START,
    FREEZE_DATE,
    RQ3_PORTFOLIOS,
    TICKERS,
)

# ---------------------------------------------------------------------------
# 1) Visual Style (Aligned with 05_plot_rq1.py with extra label spacing)
# ---------------------------------------------------------------------------
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

PALETTE = {
    "P1: Pure USD 60/40 (60% SPY / 40% AGG)": "#eb6834",  # Orange
    "P1b: Treasury 60/40 (60% SPY / 40% IEF)": "#d95f02",  # Dark Orange
    "P2: Moderate Gold (60% SPY / 30% AGG / 10% GLD)": "#1baf7a",  # Green
    "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)": "#2a78d6",  # Blue
    "P4: Currency Safe-Haven (60% SPY / 20% AGG / 10% FXF / 10% FXY)": "#898781",  # Grey
    "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)": "#e34948",  # Red
    "P6: Global De-dollarized (40% SPY / 10% EFA / 10% EEM / 15% AGG / 10% BWX / 15% GLD)": "#6250d6",  # Purple
    "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)": "#eda100",  # Gold
}

SHORT_LABELS = {
    "P1: Pure USD 60/40 (60% SPY / 40% AGG)": "P1: Pure USD 60/40 (AGG)",
    "P1b: Treasury 60/40 (60% SPY / 40% IEF)": "P1b: Treasury 60/40 (IEF)",
    "P2: Moderate Gold (60% SPY / 30% AGG / 10% GLD)": "P2: Moderate Gold (10% GLD)",
    "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)": "P3: Aggressive Gold (20% GLD)",
    "P4: Currency Safe-Haven (60% SPY / 20% AGG / 10% FXF / 10% FXY)": "P4: FX Safe-Haven (FXF+FXY)",
    "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)": "P5: Non-USD Bonds (20% BWX)",
    "P6: Global De-dollarized (40% SPY / 10% EFA / 10% EEM / 15% AGG / 10% BWX / 15% GLD)": "P6: Global De-dollarized",
    "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)": "P7: Equal-Weight (SPY/AGG/GLD)",
}

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
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def finish(fig, name, title, subtitle, source, note=None, bottom_offset=-18):
    """Consistent header/footer layout with generous vertical spacing to prevent overlap."""
    above = lambda pts: offset_copy(fig.transFigure, fig=fig, y=pts, units="points")
    fig.text(
        0.01,
        1.0,
        subtitle,
        transform=above(8),
        ha="left",
        va="bottom",
        fontsize=9,
        color=INK2,
    )
    fig.text(
        0.01,
        1.0,
        title,
        transform=above(24),
        ha="left",
        va="bottom",
        fontsize=11.5,
        fontweight="bold",
        color=INK,
    )
    foot = f"Source: {source}" + (f"\nNote: {note}" if note else "")
    fig.text(
        0.01,
        0.0,
        foot,
        transform=above(bottom_offset),
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED,
    )
    out = FIG_RQ3 / f"{name}.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"  saved fig_rq3/{out.name}")


# ---------------------------------------------------------------------------
# 2) Load & Align Cleaned Data
# ---------------------------------------------------------------------------
def load_aligned_data():
    rets = pd.read_csv(CLEAN / "returns_monthly.csv")
    macro = pd.read_csv(CLEAN / "macro_monthly.csv")

    # Interpolate the single missing CPI value (2025-10) before computing monthly inflation
    macro["CPIAUCSL_clean"] = macro["CPIAUCSL"].interpolate(method="linear")
    macro["cpi_inf"] = macro["CPIAUCSL_clean"].pct_change()
    macro["myr_ret"] = macro["DEXMAUS_monthend"].pct_change()
    macro["usd_ret"] = macro["DTWEXBGS_monthend"].pct_change()

    df = pd.merge(
        rets,
        macro[["date", "cpi_inf", "myr_ret", "usd_ret", "GS10", "TB3MS"]],
        on="date",
        how="left",
    )
    df.index = pd.PeriodIndex(df["date"], freq="M").to_timestamp(how="end").normalize()
    return df


# ---------------------------------------------------------------------------
# 3) Portfolio Rebalancing & Metric Engines
# ---------------------------------------------------------------------------
def simulate_portfolio(sub_df, w_dict, rule="annual"):
    """
    Simulates a multi-asset portfolio with explicit weight drift.
    rule: 'annual' (reset every January - Main Result),
          'monthly' (reset every month - Robustness Check),
          'buy_and_hold' (never reset - Drift Comparison).
    """
    cols = list(w_dict.keys())
    target_w = np.array([w_dict[c] for c in cols], dtype=float)
    target_w /= target_w.sum()

    curr_w = target_w.copy()
    p_rets = []
    w_hist = []

    for i, (dt_idx, row) in enumerate(sub_df.iterrows()):
        if i == 0:
            curr_w = target_w.copy()
        elif rule == "monthly":
            curr_w = target_w.copy()
        elif rule == "annual" and dt_idx.month == 1:
            curr_w = target_w.copy()

        r_vec = np.array([row[c] for c in cols], dtype=float)
        p_r = np.dot(curr_w, r_vec)
        p_rets.append(p_r)

        grown = curr_w * (1.0 + r_vec)
        curr_w = grown / grown.sum()
        w_hist.append(curr_w.copy())

    ret_series = pd.Series(p_rets, index=sub_df.index)
    drift_df = pd.DataFrame(w_hist, index=sub_df.index, columns=cols)
    return ret_series, drift_df


def compute_metrics(s, rf):
    s = s.dropna()
    rf = rf.loc[s.index]
    n = len(s)
    cum = (1 + s).prod() - 1
    cagr = (1 + cum) ** (12.0 / n) - 1
    vol = s.std(ddof=1) * np.sqrt(12)
    ex = s - rf
    ann_ex = ex.mean() * 12
    sharpe = ann_ex / vol if vol > 0 else np.nan
    down = np.minimum(0, ex)
    d_dev = np.sqrt(np.mean(down**2)) * np.sqrt(12)
    sortino = ann_ex / d_dev if d_dev > 0 else np.nan
    w = (1 + s).cumprod()
    mdd = ((w - w.cummax()) / w.cummax()).min()
    calmar = cagr / abs(mdd) if mdd != 0 else np.nan
    var95 = np.percentile(s, 5)
    return pd.Series(
        {
            "CumRet(%)": cum * 100,
            "CAGR(%)": cagr * 100,
            "AnnVol(%)": vol * 100,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "MaxDD(%)": mdd * 100,
            "Calmar": calmar,
            "VaR95(%)": var95 * 100,
        }
    )


# ---------------------------------------------------------------------------
# 4) Export Summary Tables (CSV)
# ---------------------------------------------------------------------------
def generate_tables(df):
    assets = list(TICKERS.keys())
    df_18 = df.loc["2018-01-01":"2025-12-31"]
    df_08 = df.loc["2008-01-01":"2025-12-31"]
    df_pre = df.loc["2018-01-01":"2022-01-31"]
    df_post = df.loc["2022-02-01":"2025-12-31"]

    # Table 1: Standalone Assets (2018-2025 & 2008-2025 + USD Sensitivity)
    sa_rows = {}
    for a in assets:
        m18 = compute_metrics(df_18[a], df_18["RF"])
        mpost = compute_metrics(df_post[a], df_post["RF"])
        m08 = compute_metrics(df_08[a], df_08["RF"])
        m18["PostFreeze_CAGR(%)"] = mpost["CAGR(%)"]
        m18["PostFreeze_Sharpe"] = mpost["Sharpe"]
        m18["Corr_vs_USD_Index"] = df_18[a].corr(df_18["usd_ret"])
        m18["CAGR_2008_2025(%)"] = m08["CAGR(%)"]
        m18["Sharpe_2008_2025"] = m08["Sharpe"]
        sa_rows[a] = m18
    t1 = pd.DataFrame(sa_rows).T.round(2)
    t1.to_csv(TABLES_RQ3 / "table_3_3_1_standalone_assets.csv")

    # Table 2: Portfolios 2018-2025 (Annual Main vs Monthly & Buy-and-Hold Robustness)
    p18_rows = {}
    for pname, wdict in RQ3_PORTFOLIOS.items():
        s_ann, _ = simulate_portfolio(df_18, wdict, rule="annual")
        s_mon, _ = simulate_portfolio(df_18, wdict, rule="monthly")
        s_bh, _ = simulate_portfolio(df_18, wdict, rule="buy_and_hold")
        s_pre, _ = simulate_portfolio(df_pre, wdict, rule="annual")
        s_post, _ = simulate_portfolio(df_post, wdict, rule="annual")

        m = compute_metrics(s_ann, df_18["RF"])
        m_mon = compute_metrics(s_mon, df_18["RF"])
        m_bh = compute_metrics(s_bh, df_18["RF"])
        m["PreFreeze_Sharpe"] = compute_metrics(s_pre, df_pre["RF"])["Sharpe"]
        m["PostFreeze_Sharpe"] = compute_metrics(s_post, df_post["RF"])["Sharpe"]
        m["Monthly_CAGR(%)"] = m_mon["CAGR(%)"]
        m["Monthly_Sharpe"] = m_mon["Sharpe"]
        m["BuyHold_CAGR(%)"] = m_bh["CAGR(%)"]
        m["BuyHold_Sharpe"] = m_bh["Sharpe"]
        p18_rows[pname] = m
    t2 = pd.DataFrame(p18_rows).T.round(2)
    t2.to_csv(TABLES_RQ3 / "table_3_3_2_portfolios_2018_2025.csv")

    # Table 3: Multi-Crisis Robustness 2008-2025 (GFC 2008, COVID 2020, Freeze 2022)
    p08_rows = {}
    for pname, wdict in RQ3_PORTFOLIOS.items():
        s_08, _ = simulate_portfolio(df_08, wdict, rule="annual")
        m08 = compute_metrics(s_08, df_08["RF"])
        m08["GFC_2008_Ret(%)"] = (
            (1 + s_08.loc["2008-01-01":"2008-12-31"]).prod() - 1
        ) * 100
        m08["COVID_2020_Ret(%)"] = (
            (1 + s_08.loc["2020-01-01":"2020-12-31"]).prod() - 1
        ) * 100
        m08["Freeze_2022_Ret(%)"] = (
            (1 + s_08.loc["2022-01-01":"2022-12-31"]).prod() - 1
        ) * 100
        p08_rows[pname] = m08
    t3 = pd.DataFrame(p08_rows).T.round(2)
    t3.to_csv(TABLES_RQ3 / "table_3_3_3_multicrisis_2008_2025.csv")

    # Table 4: Real (CPI-Adjusted) & Malaysian Ringgit (MYR) Perspectives (2018-2025)
    real_myr_rows = {}
    for pname, wdict in RQ3_PORTFOLIOS.items():
        s_ann, _ = simulate_portfolio(df_18, wdict, rule="annual")
        m_nom = compute_metrics(s_ann, df_18["RF"])

        s_real = (1 + s_ann) / (1 + df_18["cpi_inf"]) - 1
        rf_real = (1 + df_18["RF"]) / (1 + df_18["cpi_inf"]) - 1
        m_real = compute_metrics(s_real, rf_real)

        s_myr = (1 + s_ann) * (1 + df_18["myr_ret"]) - 1
        m_myr = compute_metrics(s_myr, df_18["RF"])

        real_myr_rows[pname] = pd.Series(
            {
                "Nom_USD_CAGR(%)": m_nom["CAGR(%)"],
                "Nom_USD_Sharpe": m_nom["Sharpe"],
                "Real_USD_CAGR(%)": m_real["CAGR(%)"],
                "Real_USD_Sharpe": m_real["Sharpe"],
                "MYR_CAGR(%)": m_myr["CAGR(%)"],
                "MYR_AnnVol(%)": m_myr["AnnVol(%)"],
                "MYR_MaxDD(%)": m_myr["MaxDD(%)"],
            }
        )
    t4 = pd.DataFrame(real_myr_rows).T.round(2)
    t4.to_csv(TABLES_RQ3 / "table_3_3_4_real_and_myr_returns.csv")
    print(f"  saved 4 summary CSV tables to {TABLES_RQ3}")


# ---------------------------------------------------------------------------
# 5) Figures (Saved to fig_rq3/ without 'fig_rq1' prefix)
# ---------------------------------------------------------------------------
def fig_01_wealth_drawdown(df):
    df_18 = df.loc["2018-01-01":"2025-12-31"]
    selected = [
        "P1: Pure USD 60/40 (60% SPY / 40% AGG)",
        "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)",
        "P4: Currency Safe-Haven (60% SPY / 20% AGG / 10% FXF / 10% FXY)",
        "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)",
        "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)",
    ]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(8.5, 5.8), gridspec_kw={"height_ratios": [1.8, 1]}, sharex=True
    )
    freeze_dt = pd.Timestamp("2022-02-28")

    for pname in selected:
        s_ann, _ = simulate_portfolio(df_18, RQ3_PORTFOLIOS[pname], rule="annual")
        wealth = 100 * (1 + s_ann).cumprod()
        dd = ((wealth - wealth.cummax()) / wealth.cummax()) * 100
        ax1.plot(df_18.index, wealth, color=PALETTE[pname], label=SHORT_LABELS[pname])
        ax2.plot(df_18.index, dd, color=PALETTE[pname], lw=1.6)

    for ax in (ax1, ax2):
        ax.axvline(freeze_dt, color=MUTED, lw=0.9, ls=(0, (3, 3)), zorder=1)

    ax1.annotate(
        "Russian reserves\nfrozen (Feb 2022)",
        xy=(mdates.date2num(freeze_dt), 0.94),
        xycoords=ax1.get_xaxis_transform(),
        xytext=(5, 0),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED,
    )
    ax1.set_ylabel("Portfolio Value ($100 base)")
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax2.set_ylabel("Drawdown (%)")
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax2.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2018, 2026)])
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax1.legend(loc="upper left", ncol=1, fontsize=8)
    fig.tight_layout()
    finish(
        fig,
        "01_wealth_drawdown",
        "Gold reallocation boosted wealth and cushioned drawdowns; fiat alternatives lagged",
        "Cumulative growth of $100 (top) and drawdown from peak (bottom), annually rebalanced, Jan 2018 – Dec 2025",
        "Author calculations from Yahoo Finance (SPY, AGG, GLD, FXF, FXY, BWX) via returns_monthly.csv.",
        "Portfolios are rebalanced annually every January; transaction costs and taxes are excluded.",
        bottom_offset=-14,
    )


def fig_02_rolling_correlations(df):
    sub = df.loc["2016-02-01":"2025-12-31"]
    roll_agg = sub["SPY"].rolling(24).corr(sub["AGG"]).loc["2018-01-01":]
    roll_ief = sub["SPY"].rolling(24).corr(sub["IEF"]).loc["2018-01-01":]
    roll_gld = sub["SPY"].rolling(24).corr(sub["GLD"]).loc["2018-01-01":]

    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    ax.plot(
        roll_ief.index,
        roll_ief,
        color="#eb6834",
        label="SPY vs. IEF (7–10Y U.S. Treasuries)",
    )
    ax.plot(
        roll_agg.index,
        roll_agg,
        color="#e34948",
        ls=(0, (4, 2)),
        lw=1.7,
        label="SPY vs. AGG (U.S. Aggregate Bonds)",
    )
    ax.plot(
        roll_gld.index, roll_gld, color="#2a78d6", label="SPY vs. GLD (Physical Gold)"
    )

    ax.axhline(0, color=INK2, lw=0.8)
    freeze_dt = pd.Timestamp("2022-02-28")
    ax.axvline(freeze_dt, color=MUTED, lw=0.9, ls=(0, (3, 3)))
    ax.annotate(
        "Feb 2022 reserve freeze &\nFed rate-hiking cycle",
        xy=(mdates.date2num(freeze_dt), 0.94),
        xycoords=ax.get_xaxis_transform(),
        xytext=(5, 0),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED,
    )
    ax.set_ylim(-0.75, 0.90)
    ax.set_ylabel("24-Month Rolling Correlation (r)")
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2018, 2026)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    finish(
        fig,
        "02_rolling_correlations",
        "Stock–bond correlations flipped strongly positive after 2022, eroding bond hedging power",
        "Rolling 24-month Pearson correlation with U.S. equities (SPY), Jan 2018 – Dec 2025",
        "Author calculations from returns_monthly.csv (SPY, AGG, IEF, GLD).",
        "Values above zero indicate assets move in the same direction as U.S. stocks, reducing diversification.",
        bottom_offset=-28,
    )


def fig_03_dollar_sensitivity(df):
    df_18 = df.loc["2018-01-01":"2025-12-31"]
    weak = df_18[df_18["usd_ret"] < 0]
    strong = df_18[df_18["usd_ret"] >= 0]

    assets = ["GLD", "EEM", "EFA", "SPY", "BWX", "FXF", "AGG", "FXY", "IEF"]
    weak_means = [weak[a].mean() * 100 for a in assets]
    strong_means = [strong[a].mean() * 100 for a in assets]

    x = np.arange(len(assets))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    b1 = ax.bar(
        x - w / 2,
        weak_means,
        width=w,
        color="#2a78d6",
        label="Months when USD Index weakens (n = 50)",
    )
    b2 = ax.bar(
        x + w / 2,
        strong_means,
        width=w,
        color="#e34948",
        label="Months when USD Index strengthens (n = 46)",
    )

    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(assets, fontweight="bold")
    ax.set_ylabel("Mean Monthly Return (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
    ax.set_ylim(-3.6, 4.4)

    for bar in b1:
        v = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.12,
            f"{v:+.1f}%",
            ha="center",
            va="bottom",
            fontsize=7.2,
            color=INK,
        )
    for bar in b2:
        v = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v - 0.15,
            f"{v:+.1f}%",
            ha="center",
            va="top",
            fontsize=7.2,
            color=INK,
        )

    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    finish(
        fig,
        "03_dollar_sensitivity",
        "Gold captured upside when the U.S. dollar weakened without suffering severe strong-dollar drag",
        "Average monthly total return (%) during weakening vs. strengthening Broad U.S. Dollar Index (DTWEXBGS) months, 2018–2025",
        "Author calculations from returns_monthly.csv and FRED DTWEXBGS (macro_monthly.csv).",
        "Non-USD fiat assets (EEM, EFA, BWX, FXY, FXF) gained when the dollar fell but suffered heavy losses when the dollar rose.",
        bottom_offset=-28,
    )


def fig_04_efficient_frontier(df):
    df_18 = df.loc["2018-01-01":"2025-12-31"]

    def trace_frontier(asset_list, n_pts=45):
        mu = df_18[asset_list].mean() * 12
        cov = df_18[asset_list].cov() * 12
        n = len(asset_list)
        targets = np.linspace(mu.min(), mu.max(), n_pts)
        vols, rets = [], []
        for tr in targets:
            cons = (
                {"type": "eq", "fun": lambda w: np.sum(w) - 1},
                {"type": "eq", "fun": lambda w: np.dot(w, mu) - tr},
            )
            res = minimize(
                lambda w: np.sqrt(np.dot(w.T, np.dot(cov, w))),
                np.repeat(1 / n, n),
                method="SLSQP",
                bounds=[(0, 1)] * n,
                constraints=cons,
            )
            if res.success:
                vols.append(res.fun * 100)
                rets.append(tr * 100)
        return np.array(vols), np.array(rets)

    v_usd, r_usd = trace_frontier(["SPY", "AGG", "IEF"])
    v_all, r_all = trace_frontier(
        ["SPY", "AGG", "IEF", "GLD", "EFA", "EEM", "BWX", "FXF"]
    )

    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    ax.plot(
        v_usd,
        r_usd,
        color="#eb6834",
        ls=(0, (4, 2)),
        lw=2.0,
        label="USD-Only Frontier (SPY + AGG + IEF)",
    )
    ax.plot(
        v_all,
        r_all,
        color="#2a78d6",
        lw=2.4,
        label="Expanded Multi-Asset Frontier (Incl. Gold & Non-USD)",
    )

    pts = [
        ("P1: Pure USD 60/40 (60% SPY / 40% AGG)", (6, -8)),
        ("P2: Moderate Gold (60% SPY / 30% AGG / 10% GLD)", (6, -2)),
        ("P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)", (6, 4)),
        ("P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)", (6, -6)),
        ("P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)", (-8, 8)),
    ]
    for pname, offset in pts:
        s_ann, _ = simulate_portfolio(df_18, RQ3_PORTFOLIOS[pname], rule="annual")
        m = compute_metrics(s_ann, df_18["RF"])
        ax.scatter(m["AnnVol(%)"], m["CAGR(%)"], color=PALETTE[pname], s=55, zorder=5)
        ax.annotate(
            SHORT_LABELS[pname].split("(")[0].strip(),
            xy=(m["AnnVol(%)"], m["CAGR(%)"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=7.8,
            fontweight="bold",
            color=INK,
        )

    ax.set_xlabel("Annualized Volatility (Standard Deviation, %)")
    ax.set_ylabel("Annualized Return (CAGR / Mean, %)")
    ax.set_xlim(5.0, 16.5)
    ax.set_ylim(1.0, 16.5)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    finish(
        fig,
        "04_efficient_frontier",
        "Allocating to physical gold shifts the Markowitz Efficient Frontier upward and leftward",
        "Mean-variance efficient frontiers and annually rebalanced model portfolios, Jan 2018 – Dec 2025",
        "Author Markowitz quadratic optimization from returns_monthly.csv.",
        "Short-selling is constrained (weights >= 0, sum of weights = 1).",
        bottom_offset=-14,
    )


def fig_05_multi_crisis_2008_2025(df):
    df_08 = df.loc["2008-01-01":"2025-12-31"]
    selected = [
        "P1: Pure USD 60/40 (60% SPY / 40% AGG)",
        "P1b: Treasury 60/40 (60% SPY / 40% IEF)",
        "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)",
        "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)",
        "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)",
    ]

    crisis_data = []
    for pname in selected:
        s_08, _ = simulate_portfolio(df_08, RQ3_PORTFOLIOS[pname], rule="annual")
        r08 = ((1 + s_08.loc["2008-01-01":"2008-12-31"]).prod() - 1) * 100
        r20 = ((1 + s_08.loc["2020-01-01":"2020-12-31"]).prod() - 1) * 100
        r22 = ((1 + s_08.loc["2022-01-01":"2022-12-31"]).prod() - 1) * 100
        crisis_data.append(
            {
                "Portfolio": SHORT_LABELS[pname],
                "2008 GFC": r08,
                "2020 COVID-19": r20,
                "2022 Freeze & Rate Shock": r22,
            }
        )

    cdf = pd.DataFrame(crisis_data).set_index("Portfolio")
    x = np.arange(len(cdf))
    w = 0.25

    fig, ax = plt.subplots(figsize=(8.5, 3.9))
    b1 = ax.bar(
        x - w,
        cdf["2008 GFC"],
        width=w,
        color="#52514e",
        label="2008 Global Financial Crisis (Deflationary)",
    )
    b2 = ax.bar(
        x,
        cdf["2020 COVID-19"],
        width=w,
        color="#1baf7a",
        label="2020 COVID-19 Liquidity Shock",
    )
    b3 = ax.bar(
        x + w,
        cdf["2022 Freeze & Rate Shock"],
        width=w,
        color="#e34948",
        label="2022 Reserve Freeze & Inflation Shock",
    )

    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cdf.index, fontsize=7.8)
    ax.set_ylabel("Calendar-Year Return (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_ylim(-25, 23)

    for bars in (b1, b2, b3):
        for bar in bars:
            v = bar.get_height()
            va = "bottom" if v >= 0 else "top"
            offset = 0.5 if v >= 0 else -0.6
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + offset,
                f"{v:+.1f}%",
                ha="center",
                va=va,
                fontsize=6.8,
                color=INK,
            )

    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout()
    finish(
        fig,
        "05_multi_crisis_2008_2025",
        "Treasuries cushioned the 2008 GFC, but only gold protected portfolios in the 2022 shock",
        "Calendar-year portfolio total returns (%) across three distinct macroeconomic crises (2008–2025 sample)",
        "Author calculations from returns_monthly.csv (Jan 2008 – Dec 2025, annually rebalanced).",
        "In 2008 (deflationary crash), U.S. Treasuries (IEF) rallied; in 2022 (inflation/sanction shock), both stocks and bonds fell together.",
        bottom_offset=-30,
    )


def fig_06_real_vs_myr_returns(df):
    df_18 = df.loc["2018-01-01":"2025-12-31"]
    selected = [
        "P1: Pure USD 60/40 (60% SPY / 40% AGG)",
        "P2: Moderate Gold (60% SPY / 30% AGG / 10% GLD)",
        "P3: Aggressive Gold (60% SPY / 20% AGG / 20% GLD)",
        "P4: Currency Safe-Haven (60% SPY / 20% AGG / 10% FXF / 10% FXY)",
        "P5: Non-USD Bond Shift (60% SPY / 20% AGG / 20% BWX)",
        "P6: Global De-dollarized (40% SPY / 10% EFA / 10% EEM / 15% AGG / 10% BWX / 15% GLD)",
        "P7: Equal-Weight Safe-Haven (33.3% SPY / 33.3% AGG / 33.3% GLD)",
    ]

    rows = []
    for pname in selected:
        s_ann, _ = simulate_portfolio(df_18, RQ3_PORTFOLIOS[pname], rule="annual")
        s_real = (1 + s_ann) / (1 + df_18["cpi_inf"]) - 1
        s_myr = (1 + s_ann) * (1 + df_18["myr_ret"]) - 1
        rows.append(
            {
                "Portfolio": SHORT_LABELS[pname].split("(")[0].strip(),
                "Nominal USD": compute_metrics(s_ann, df_18["RF"])["CAGR(%)"],
                "Real USD (CPI-Adjusted)": compute_metrics(s_real, df_18["RF"])[
                    "CAGR(%)"
                ],
                "MYR MaxDD": abs(compute_metrics(s_myr, df_18["RF"])["MaxDD(%)"]),
                "USD MaxDD": abs(compute_metrics(s_ann, df_18["RF"])["MaxDD(%)"]),
            }
        )
    res = pd.DataFrame(rows).set_index("Portfolio")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.8), sharey=True)
    y = np.arange(len(res))
    h = 0.36

    # Left panel: Nominal vs Real (CPI-Adjusted) CAGR
    ax1.barh(
        y - h / 2,
        res["Nominal USD"],
        height=h,
        color="#2a78d6",
        label="Nominal USD CAGR",
    )
    ax1.barh(
        y + h / 2,
        res["Real USD (CPI-Adjusted)"],
        height=h,
        color="#1baf7a",
        label="Real (After-Inflation) CAGR",
    )
    ax1.set_yticks(y)
    ax1.set_yticklabels(res.index, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlabel("Annualized Return (CAGR, %)")
    ax1.set_xlim(0, 15.0)
    ax1.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax1.grid(axis="x", visible=True)
    ax1.grid(axis="y", visible=False)
    ax1.set_title(
        "Purchasing Power (Nominal vs. Real CAGR)",
        loc="left",
        fontsize=9.5,
        fontweight="bold",
    )
    ax1.legend(loc="lower right", fontsize=7.5)

    # Right panel: USD vs MYR Maximum Drawdown magnitude
    ax2.barh(
        y - h / 2,
        res["USD MaxDD"],
        height=h,
        color="#e34948",
        label="Max Drawdown in USD (%)",
    )
    ax2.barh(
        y + h / 2,
        res["MYR MaxDD"],
        height=h,
        color="#eda100",
        label="Max Drawdown in MYR (%)",
    )
    ax2.set_xlabel("Maximum Peak-to-Trough Drawdown Magnitude (%)")
    ax2.set_xlim(0, 26.0)
    ax2.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax2.grid(axis="x", visible=True)
    ax2.grid(axis="y", visible=False)
    ax2.set_title(
        "Malaysian Investor Currency Cushion (Max Drawdown)",
        loc="left",
        fontsize=9.5,
        fontweight="bold",
    )
    ax2.legend(loc="lower right", fontsize=7.5)

    fig.tight_layout()
    finish(
        fig,
        "06_real_vs_myr_returns",
        "Gold preserved real purchasing power and compressed drawdowns for Malaysian Ringgit investors",
        "Nominal vs. U.S. CPI-adjusted real CAGR (left) and USD vs. MYR maximum drawdown magnitude (right), 2018–2025",
        "Author calculations from returns_monthly.csv and FRED CPIAUCSL / DEXMAUS (macro_monthly.csv).",
        "U.S. CPI inflation averaged 3.49% p.a. (2018–2025). USD appreciation during global sell-offs cushioned drawdowns in MYR terms.",
        bottom_offset=-16,
    )


def main():
    print("Loading aligned RQ3 datasets...")
    df = load_aligned_data()
    print("Computing RQ3 summary tables...")
    generate_tables(df)
    print("Drawing RQ3 figures into fig_rq3/...")
    fig_01_wealth_drawdown(df)
    fig_02_rolling_correlations(df)
    fig_03_dollar_sensitivity(df)
    fig_04_efficient_frontier(df)
    fig_05_multi_crisis_2008_2025(df)
    fig_06_real_vs_myr_returns(df)
    print(f"\nAll RQ3 deliverables completed! Check {FIG_RQ3} and {TABLES_RQ3}")


if __name__ == "__main__":
    main()
