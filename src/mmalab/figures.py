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
    s = pd.read_csv(OUT / "card_quality_summary.csv")
    s = s[s["year"] >= 2022]
    years = sorted(s["year"].unique())
    x = np.arange(len(years))
    w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))

    for ax, col, title, fmt in [
        (axes[0], "top10_bouts_per_card", "Top-10 vs top-10 bouts per card", "{:.1f}"),
        (axes[1], "share_cards_zero_top10", "Share of cards with zero top-10 bouts", "{:.0%}"),
    ]:
        for i, (ctype, color) in enumerate([("Numbered", BLUE), ("Fight Night", ORANGE)]):
            d = s[s["card_type"] == ctype].set_index("year").reindex(years)[col].fillna(0)
            bars = ax.bar(x + (i - 0.5) * w, d.values, width=w - 0.04, color=color, label=ctype, linewidth=0)
            for b, v in zip(bars, d.values):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02 * ax.get_ylim()[1] if False else b.get_height(),
                        fmt.format(v), ha="center", va="bottom", fontsize=8.5, color=INK2)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{y}" + (" YTD" if y == max(years) else "") for y in years])
        ax.set_title(title, loc="left", fontsize=11)
        ax.grid(axis="x", visible=False)
        if col.startswith("share"):
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    for ax in axes:
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    axes[0].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=9)
    fig.suptitle("Ranked matchmaking is concentrated on numbered cards (UFC, 2022-2026)",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.text(0.01, 0.005, "Position = rank among active fighters by pre-fight performance-adjusted Elo; "
             "top 10 = positions 1-11 (champion plus ten). Source: UFCStats via open scrapers.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
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


def backtest_table() -> None:
    rep = json.loads((OUT / "backtest_report.json").read_text())
    mk = rep["market_comparison_2014_2023"]
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
    lines = ["| Model | Log loss, tune 2010-19 | Log loss, test 2020-26 | Brier, test | Accuracy, test |",
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
