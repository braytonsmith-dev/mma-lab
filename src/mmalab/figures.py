"""
figures.py - Static figures for the paper and README.

  outputs/fig_card_quality.png   top-10 bouts per card, numbered vs Fight Night, by year
  outputs/fig_backtest.png       log loss by model and year, plus calibration on the test window
  outputs/table_backtest.md      the comparison table used in the abstract
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"

# reference palette (validated adjacent pair): slot 1 blue, slot 2 orange
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
})


def card_quality_figure() -> None:
    """Figure 1: champion-or-top-10 bouts by card type and year, split into non-title (solid) and
    title (hatched) bouts, per card and per ten scheduled bouts, with the number of cards under each bar."""
    s = pd.read_csv(OUT / "card_quality_summary.csv")
    s = s[s["year"] >= 2022]
    tot_path = OUT / "card_quality_totals.csv"
    tot = pd.read_csv(tot_path).set_index("card_type") if tot_path.exists() else None
    years = sorted(s["year"].unique())
    x = np.arange(len(years))
    w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    panels = [(axes[0], "top10_bouts_per_card", "nontitle_top10_bouts_per_card", "Per card"),
              (axes[1], "top10_per_10_bouts", "nontitle_top10_per_10_bouts", "Per ten scheduled bouts (card-size adjusted)")]
    for ax, total_col, nt_col, title in panels:
        for i, (ctype, color) in enumerate([("Numbered", BLUE), ("Fight Night", ORANGE)]):
            d = s[s["card_type"] == ctype].set_index("year").reindex(years)
            total, nontitle = d[total_col].fillna(0).values, d[nt_col].fillna(0).values
            n = d["events"].fillna(0).astype(int).values
            pos = x + (i - 0.5) * w
            ax.bar(pos, nontitle, width=w - 0.04, color=color, linewidth=0, label=f"{ctype}, non-title")
            # title bouts stacked on top: same hue, surface hatch, 2px surface gap below
            ax.bar(pos, total - nontitle, bottom=nontitle, width=w - 0.04, color=color, hatch="////",
                   edgecolor=SURFACE, linewidth=0.8, label=f"{ctype}, title bout")
            for px, t, k in zip(pos, total, n):
                ax.text(px, t, f"{t:.2f}", ha="center", va="bottom", fontsize=8.2, color=INK2)
                ax.text(px, -0.02 * max(s[total_col].max(), 1e-9), f"n={k}", ha="center", va="top", fontsize=6.5, color=MUTED)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{y}" + (" YTD" if y == max(years) else "") for y in years])
        ax.tick_params(axis="x", pad=12)
        ax.set_title(title, loc="left", fontsize=11)
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, s[total_col].max() * 1.25)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles[:4], labels[:4], frameon=False, loc="upper left", bbox_to_anchor=(0.005, 0.935), ncol=4,
               fontsize=8.5, handlelength=1.6, columnspacing=1.4)
    fig.suptitle("Champion-or-top-10 bouts concentrate on numbered cards, with or without title bouts",
                 x=0.01, y=0.985, ha="left", fontsize=12, color=INK)
    sub = ""
    if tot is not None:
        nb, fn = tot.loc["Numbered"], tot.loc["Fight Night"]
        sub = (f"2022 to Sept 2026, {int(nb['events']) + int(fn['events'])} cards: numbered {nb['top10_bouts_per_card']:.2f} per card "
               f"({nb['nontitle_top10_bouts_per_card']:.2f} non-title) vs Fight Night {fn['top10_bouts_per_card']:.2f} "
               f"({fn['nontitle_top10_bouts_per_card']:.2f}); {fn['share_cards_zero_top10']:.0%} of Fight Nights had none.")
    fig.text(0.01, 0.058, sub, fontsize=8.2, color=INK2)
    fig.text(0.01, 0.03, "Champion-or-top-10 bout = both fighters inside positions 1-11 of their division among fighters active in the "
             "prior 18 months, by pre-fight performance-adjusted Elo.", fontsize=7.2, color=MUTED)
    fig.text(0.01, 0.006, "n = cards. Hatched = title bouts (the champion is in every title bout). Source: UFCStats; "
             "outputs/card_quality_events.csv.", fontsize=7.2, color=MUTED)
    fig.tight_layout(rect=(0, 0.085, 1, 0.885))
    fig.savefig(OUT / "fig_card_quality.png", dpi=200)
    plt.close(fig)


def backtest_figure() -> None:
    rep = json.loads((OUT / "backtest_report.json").read_text())
    by_year = pd.read_csv(OUT / "elo_by_year.csv")
    cal = pd.read_csv(OUT / "calibration_test_2020_2026.csv")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    ax = axes[0]
    ax.plot(by_year["date"], by_year["log_loss"], color=BLUE, linewidth=2, marker="o", markersize=5,
            label="Performance-adjusted Elo")
    ax.axhline(0.6931, color=MUTED, linewidth=1, linestyle="--")
    ax.text(by_year["date"].min(), 0.6931 + 0.001, "coin flip 0.693", fontsize=8, color=MUTED, va="bottom")
    ax.axhline(rep["market_comparison_2014_2023"]["market_devigged"]["log_loss"], color=ORANGE, linewidth=1.2)
    ax.text(by_year["date"].min(), rep["market_comparison_2014_2023"]["market_devigged"]["log_loss"] + 0.001,
            "betting market (2014-2023 avg)", fontsize=8, color=ORANGE, va="bottom")
    ax.axvspan(2019.5, by_year["date"].max() + 0.5, color=GRID, alpha=0.5, linewidth=0)
    ax.text(2019.7, 0.6895, "held-out test window (parameters fixed on 2010-19)", fontsize=8, color=INK2, va="top")
    ax.set_title("Out-of-sample log loss by year (lower is better)", loc="left", fontsize=11)
    ax.set_xticks(by_year["date"].astype(int))
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", visible=False)

    ax = axes[1]
    ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1, linestyle="--")
    sizes = 20 + 200 * cal["n"] / cal["n"].max()
    ax.scatter(cal["predicted"], cal["actual"], s=sizes, color=BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    ax.set_xlabel("Predicted win probability")
    ax.set_ylabel("Observed win rate")
    ax.set_title("Calibration, 2020-2026 test bouts (dot size = count)", loc="left", fontsize=11)
    ax.set_xlim(0.1, 0.9)
    ax.set_ylim(0.1, 0.9)
    fig.suptitle("Adding in-fight statistics to Elo improves UFC bout prediction out of sample",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "fig_backtest.png", dpi=200)
    plt.close(fig)


def abstract_table() -> str:
    """Table 1 for the abstract: one pre-registered specification, paired significance, and the market
    on exactly the held-out bouts that have closing odds."""
    rep = json.loads((OUT / "backtest_report.json").read_text())
    sig, mt = rep.get("significance_classic_vs_tuned"), rep.get("market_comparison_heldout_2020_2023")
    if not sig or not mt:
        return ""
    ct, pt = rep["classic_tuned_test"], rep["tuned_test"]
    lo, hi = sig["ci95_event_block_bootstrap"]
    p = sig["mcnemar_exact_p"]
    p_txt = f"{p:.3f}" if p >= 0.001 else "< 0.001"
    n_all, n_odds = f"{pt['n']:,}", f"{mt['matched_bouts']:,}*"
    lines = [
        f"Table 1. Held-out prediction, 2020-2026. Parameters fixed by a {rep['grid']['combinations']}-point grid on "
        f"2010-2019 ({rep['tuned_tune']['n']:,} bouts); the selected specification was scored once on the held-out bouts.",
        "",
        "| Model | Bouts | Log loss | Change vs results-only (95% event-block bootstrap CI) | Brier | Accuracy | McNemar p |",
        "|---|---|---|---|---|---|---|",
        f"| Results-only Elo | {n_all} | {ct['log_loss']:.3f} | | {ct['brier']:.3f} | {ct['accuracy']:.1%} | |",
        f"| Performance-adjusted Elo | {n_all} | {pt['log_loss']:.3f} | -{sig['delta_log_loss']:.3f} ({-hi:.3f} to {-lo:.3f}) | "
        f"{pt['brier']:.3f} | {pt['accuracy']:.1%} | {p_txt} |",
        f"| Results-only Elo | {n_odds} | {mt['classic_tuned']['log_loss']:.3f} | | {mt['classic_tuned']['brier']:.3f} | "
        f"{mt['classic_tuned']['accuracy']:.1%} | |",
        f"| Performance-adjusted Elo | {n_odds} | {mt['performance_adjusted']['log_loss']:.3f} | | "
        f"{mt['performance_adjusted']['brier']:.3f} | {mt['performance_adjusted']['accuracy']:.1%} | |",
        f"| Closing betting market, de-vigged | {n_odds} | {mt['market_devigged']['log_loss']:.3f} | | "
        f"{mt['market_devigged']['brier']:.3f} | {mt['market_devigged']['accuracy']:.1%} | |",
        "",
        f"*Held-out bouts with closing odds, {mt['date_range'][0]} to {mt['date_range'][1]}. Log loss: coin flip 0.693; lower is better. "
        f"Accuracy: share of bouts in which the fighter given more than 50% won. McNemar: exact test on the "
        f"{sig['discordant_only_a_correct'] + sig['discordant_only_b_correct']} bouts the two models call differently "
        f"({sig['discordant_only_b_correct']} fixed, {sig['discordant_only_a_correct']} broken).",
    ]
    text = "\n".join(lines)
    (OUT / "table1_abstract.md").write_text(text)
    return text


def backtest_table() -> None:
    rep = json.loads((OUT / "backtest_report.json").read_text())
    mk = rep["market_comparison_2014_2023"]
    t1 = abstract_table()
    rows = [
        ("Coin flip", "-", "0.6931", "-", "50.0%"),
        ("Classic Elo, untuned (K=32)", rep["baseline_tune"]["log_loss"], rep["baseline_test"]["log_loss"],
         rep["baseline_test"]["brier"], f"{rep['baseline_test']['accuracy']:.1%}"),
        ("Classic Elo, tuned (results only)", rep["classic_tuned_tune"]["log_loss"], rep["classic_tuned_test"]["log_loss"],
         rep["classic_tuned_test"]["brier"], f"{rep['classic_tuned_test']['accuracy']:.1%}"),
        ("Performance-adjusted Elo, tuned", rep["tuned_tune"]["log_loss"], rep["tuned_test"]["log_loss"],
         rep["tuned_test"]["brier"], f"{rep['tuned_test']['accuracy']:.1%}"),
        ("Performance-adjusted Elo, interpretable (win/finish floors)", rep["ranking_model_tune"]["log_loss"],
         rep["ranking_model_test"]["log_loss"], rep["ranking_model_test"]["brier"],
         f"{rep['ranking_model_test']['accuracy']:.1%}"),
    ]
    lines = ([t1, "", "Full comparison (the interpretable site specification is a second model scored on the same window and "
              "is not the pre-registered result):", ""] if t1 else []) + [
             "| Model | Log loss, tune 2010-19 | Log loss, test 2020-26 | Brier, test | Accuracy, test |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    lines += ["", f"Test bouts: {rep['tuned_test']['n']:,}. Tuning bouts: {rep['tuned_tune']['n']:,}.",
              "", "Same-bout comparison against the closing betting market (de-vigged), "
              f"{mk['matched_bouts']:,} bouts, {mk['date_range'][0]} to {mk['date_range'][1]}:", "",
              "| Model | Log loss | Brier | Accuracy |", "|---|---|---|---|",
              f"| Performance-adjusted Elo | {mk['elo']['log_loss']} | {mk['elo']['brier']} | {mk['elo']['accuracy']:.1%} |",
              f"| Betting market | {mk['market_devigged']['log_loss']} | {mk['market_devigged']['brier']} | {mk['market_devigged']['accuracy']:.1%} |",
              f"| 50/50 blend | {mk['blend_50_50']['log_loss']} | {mk['blend_50_50']['brier']} | {mk['blend_50_50']['accuracy']:.1%} |"]
    (OUT / "table_backtest.md").write_text("\n".join(lines))


def main() -> None:
    card_quality_figure()
    if (OUT / "backtest_report.json").exists():
        backtest_figure()
        backtest_table()
    print("figures written to outputs/")


if __name__ == "__main__":
    main()
