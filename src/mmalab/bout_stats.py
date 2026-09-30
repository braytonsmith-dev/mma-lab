"""
bout_stats.py - Collapse round-by-round stats to one row per bout with totals
for fighter_a and fighter_b, plus a "dominance" differential per minute that
the margin-of-victory Elo variant can use.

dominance_a (per minute, from A's perspective) =
    (sig_landed_a - sig_landed_b)
  + 5  * (knockdowns_a - knockdowns_b)
  + 2  * (takedowns_a - takedowns_b)
  + 2  * (sub_attempts_a - sub_attempts_b)
  + (control_seconds_a - control_seconds_b) / 60
  all divided by fight minutes.

The weights are deliberately simple and stated up front; the backtest decides
how much of the rating update should listen to this number at all.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

EVENT_ALIASES = {
    "UFC Fight Night: Grasso vs. Shevchenko 2": "Noche UFC: Grasso vs. Shevchenko 2",
    "UFC Fight Night: Lopes vs. Silva": "Noche UFC: Lopes vs. Silva",
}

STAT_COLS = ["kd", "sig_landed", "sig_att", "tot_landed", "tot_att", "td_landed", "td_att",
             "sub_att", "rev", "ctrl_sec", "head_landed", "body_landed", "leg_landed",
             "dist_landed", "clinch_landed", "ground_landed"]


def build() -> pd.DataFrame:
    bouts = pd.read_csv(PROC / "bouts.csv", parse_dates=["date"])
    rs = pd.read_csv(PROC / "round_stats.csv")
    rs["event"] = rs["event"].replace(EVENT_ALIASES)

    tot = rs.groupby(["event", "bout", "fighter"], as_index=False)[STAT_COLS].sum()
    bouts["bout"] = bouts["fighter_a"] + " vs. " + bouts["fighter_b"]

    a = tot.rename(columns={c: f"{c}_a" for c in STAT_COLS}).rename(columns={"fighter": "fighter_a"})
    b = tot.rename(columns={c: f"{c}_b" for c in STAT_COLS}).rename(columns={"fighter": "fighter_b"})
    df = bouts.merge(a, on=["event", "bout", "fighter_a"], how="left") \
              .merge(b, on=["event", "bout", "fighter_b"], how="left")

    df["has_stats"] = df["sig_att_a"].notna() & df["sig_att_b"].notna()
    minutes = (df["fight_seconds"].clip(lower=30)) / 60.0
    df["minutes"] = minutes

    dom = ((df["sig_landed_a"] - df["sig_landed_b"])
           + 5 * (df["kd_a"] - df["kd_b"])
           + 2 * (df["td_landed_a"] - df["td_landed_b"])
           + 2 * (df["sub_att_a"] - df["sub_att_b"])
           + (df["ctrl_sec_a"] - df["ctrl_sec_b"]) / 60.0) / minutes
    df["dominance_a"] = dom.where(df["has_stats"])
    return df


def main() -> None:
    df = build()
    df.to_csv(PROC / "bouts_with_stats.csv", index=False)
    print(f"bouts: {len(df):,}; with round stats: {df['has_stats'].sum():,} "
          f"({df['has_stats'].mean():.1%}); first stats year: "
          f"{df.loc[df['has_stats'], 'date'].min().year}")
    d = df.loc[df["has_stats"] & df["result_a"].isin([0, 1])]
    # sanity: winners should have positive dominance most of the time
    agree = ((d["dominance_a"] > 0) == (d["result_a"] == 1)).mean()
    print(f"dominance sign agrees with winner: {agree:.1%}")
    print(d["dominance_a"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
