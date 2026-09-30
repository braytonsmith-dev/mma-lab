"""
card_quality.py - How much ranked-versus-ranked matchmaking does each card carry?

For every event, each bout is tagged with both fighters' division position on
the morning of the event: rank among fighters who competed in that division in
the prior `active_window_days`, ordered by pre-fight performance-adjusted Elo.
Position 1 is the top-rated active fighter (usually the champion), so
"top 10" here means positions 1-11 (champion plus ten), matching how fans
read the official board.

Per event:
  bouts, top10_bouts (both fighters inside top 11), top15_bouts (both inside
  top 16), ranked_appearances (fighters inside top 16), is_numbered.

Also: supply-side facts that test the "120 ranked fighters x 3 fights a year"
premise: how often ranked fighters actually fight and how often the opponent
is also ranked.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from mmalab.elo import EloParams, run_elo
from mmalab.rankings import RANKED_DIVISIONS

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
CFG = ROOT / "config" / "weights.yaml"

FROM_YEAR = 2022


def positions_on(hist: pd.DataFrame, date: pd.Timestamp, window_days: int) -> dict[tuple[str, str], int]:
    before = hist[hist["date"] < date]
    latest = before.groupby("fighter").tail(1)
    active = latest[latest["date"] >= date - pd.Timedelta(days=window_days)]
    active = active[active["division"].isin(RANKED_DIVISIONS)]
    out = {}
    for div, g in active.groupby("division"):
        g = g.sort_values("rating", ascending=False).reset_index(drop=True)
        for i, name in enumerate(g["fighter"], start=1):
            out[(div, name)] = i
    return out


def tag_bouts(rated: pd.DataFrame, hist: pd.DataFrame, window_days: int) -> pd.DataFrame:
    df = rated[(rated["date"].dt.year >= FROM_YEAR) & rated["division"].isin(RANKED_DIVISIONS)].copy()
    pos_a, pos_b = [], []
    for date, g in df.groupby("date"):
        pos = positions_on(hist, date, window_days)
        for r in g.itertuples():
            pos_a.append((r.Index, pos.get((r.division, r.fighter_a), 999)))
            pos_b.append((r.Index, pos.get((r.division, r.fighter_b), 999)))
    df["pos_a"] = pd.Series(dict(pos_a))
    df["pos_b"] = pd.Series(dict(pos_b))
    df["top10_bout"] = (df["pos_a"] <= 11) & (df["pos_b"] <= 11)
    df["top15_bout"] = (df["pos_a"] <= 16) & (df["pos_b"] <= 16)
    df["ranked_appearances"] = (df["pos_a"] <= 16).astype(int) + (df["pos_b"] <= 16).astype(int)
    return df


def event_table(tagged: pd.DataFrame, rated: pd.DataFrame) -> pd.DataFrame:
    all_bouts = rated[rated["date"].dt.year >= FROM_YEAR].groupby(["event", "date"]).size().rename("bouts")
    ev = tagged.groupby(["event", "date"]).agg(
        top10_bouts=("top10_bout", "sum"), top15_bouts=("top15_bout", "sum"),
        ranked_appearances=("ranked_appearances", "sum"),
        is_numbered=("is_numbered", "first"), location=("location", "first")).reset_index()
    ev = ev.merge(all_bouts.reset_index(), on=["event", "date"], how="left")
    ev["year"] = ev["date"].dt.year
    ev["card_type"] = ev["is_numbered"].map({True: "Numbered", False: "Fight Night"})
    ev["ranked_share"] = ev["ranked_appearances"] / (2 * ev["bouts"])
    return ev.sort_values("date", ascending=False)


def supply_facts(tagged: pd.DataFrame, hist: pd.DataFrame, window_days: int) -> dict:
    """For each year: fighters who started the year inside a division top 11,
    their bouts that year, and the share of those bouts against another top-11 fighter."""
    facts = {}
    for year in sorted(tagged["date"].dt.year.unique()):
        jan1 = pd.Timestamp(f"{year}-01-01")
        pos = positions_on(hist, jan1, window_days)
        top = {(d, n) for (d, n), p in pos.items() if p <= 11}
        yr = tagged[tagged["date"].dt.year == year]
        rows = []
        for (d, n) in top:
            b = yr[(yr["division"] == d) & ((yr["fighter_a"] == n) | (yr["fighter_b"] == n))]
            vs_top = ((b["fighter_a"] == n) & (b["pos_b"] <= 11)) | ((b["fighter_b"] == n) & (b["pos_a"] <= 11))
            rows.append({"fighter": n, "division": d, "bouts": len(b), "vs_top11": int(vs_top.sum())})
        s = pd.DataFrame(rows)
        days_in_year = (pd.Timestamp(f"{year}-12-31") - jan1).days + 1
        elapsed = min(days_in_year, (tagged["date"].max() - jan1).days + 1)
        facts[int(year)] = {
            "top11_fighters_on_jan1": int(len(s)),
            "mean_bouts_per_fighter": round(float(s["bouts"].mean()), 2),
            "annualized_bouts_per_fighter": round(float(s["bouts"].mean()) * days_in_year / elapsed, 2),
            "share_with_zero_bouts": round(float((s["bouts"] == 0).mean()), 3),
            "share_of_their_bouts_vs_top11": round(float(s["vs_top11"].sum() / max(s["bouts"].sum(), 1)), 3),
            "top10_vs_top10_bouts_total": int(yr["top10_bout"].sum()),
            "events": int(yr["event"].nunique()),
            "days_covered": int(elapsed),
        }
    return facts


def main() -> None:
    cfg = yaml.safe_load(CFG.read_text())
    bouts = pd.read_csv(PROC / "bouts_with_stats.csv", parse_dates=["date"])
    rated, hist = run_elo(bouts, EloParams(**cfg["elo"]))
    window = cfg["active_window_days"]

    tagged = tag_bouts(rated, hist, window)
    ev = event_table(tagged, rated)
    OUT.mkdir(exist_ok=True)
    tagged[["date", "event", "division", "fighter_a", "pos_a", "fighter_b", "pos_b", "top10_bout",
            "top15_bout", "method"]].to_csv(OUT / "card_quality_bouts.csv", index=False)
    ev.to_csv(OUT / "card_quality_events.csv", index=False)

    summary = ev.groupby(["year", "card_type"]).agg(
        events=("event", "size"), bouts_per_card=("bouts", "mean"),
        top10_bouts_per_card=("top10_bouts", "mean"), top15_bouts_per_card=("top15_bouts", "mean"),
        share_cards_zero_top10=("top10_bouts", lambda s: (s == 0).mean()),
        share_cards_zero_top15=("top15_bouts", lambda s: (s == 0).mean()),
        ranked_share_of_slots=("ranked_share", "mean")).round(3).reset_index()
    summary.to_csv(OUT / "card_quality_summary.csv", index=False)

    supply = supply_facts(tagged, hist, window)
    (OUT / "card_quality_supply.json").write_text(json.dumps(supply, indent=2))

    print(summary.to_string(index=False))
    print(json.dumps(supply, indent=2))
    print("\nMost and least stacked cards since", FROM_YEAR)
    cols = ["date", "event", "card_type", "bouts", "top10_bouts", "top15_bouts", "ranked_appearances"]
    print(ev.sort_values(["top10_bouts", "top15_bouts"], ascending=False)[cols].head(8).to_string(index=False))
    print(ev[ev["year"] >= 2025].sort_values(["top15_bouts", "top10_bouts"])[cols].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
