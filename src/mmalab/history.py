"""
history.py - Board snapshots, movement arrows and forward validation.

  snapshot(board, as_of)  -> outputs/history/board_<as_of>.csv
  backfill(months)        -> rebuilds the board as it stood the day before each event
                             in the last `months` and saves each snapshot
  validate()              -> for every bout after a snapshot (until the next one) between two
                             fighters on that division's board, did the higher-placed one win?
                             Compared with the official UFC media panel's order on the same bouts.
Writes outputs/forward_validation.csv and outputs/forward_validation.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from mmalab import resume_board
from mmalab.official_ranks import OfficialRanks

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
HIST = OUT / "history"
PROC = ROOT / "data" / "processed"


def board_position(row) -> int:
    if row["champion"]:
        return 0
    if row.get("interim", False) or row.get("reserved", False):
        return 0
    return int(row["rank"])


def snapshot(board: pd.DataFrame, as_of: pd.Timestamp) -> Path:
    HIST.mkdir(parents=True, exist_ok=True)
    b = board.copy()
    b["position"] = b.apply(board_position, axis=1)
    path = HIST / f"board_{pd.Timestamp(as_of).date()}.csv"
    b[["division", "fighter", "position", "rank", "score"]].to_csv(path, index=False)
    return path


def backfill(months: int = 12) -> list[Path]:
    bouts = pd.read_csv(PROC / "bouts.csv", parse_dates=["date"])
    last = bouts["date"].max()
    events = sorted(bouts.loc[bouts["date"] > last - pd.DateOffset(months=months), "date"].unique())
    paths = []
    for ev in events:
        board, meta = resume_board.build(as_of=str(pd.Timestamp(ev).date()), stability=False)
        paths.append(snapshot(board, pd.Timestamp(ev) - pd.Timedelta(days=1)))
    board, meta = resume_board.build(stability=False)
    paths.append(snapshot(board, meta["as_of"]))
    return paths


def previous_positions(before: pd.Timestamp) -> dict:
    """Positions from the latest snapshot strictly before `before`."""
    snaps = sorted(HIST.glob("board_*.csv"))
    prior = [p for p in snaps if pd.Timestamp(p.stem.split("_")[1]) < pd.Timestamp(before)]
    if not prior:
        return {}
    d = pd.read_csv(prior[-1])
    return {(r.division, r.fighter): int(r.position) for r in d.itertuples()}


def validate(board_size: int = 15) -> dict:
    bouts = pd.read_csv(PROC / "bouts.csv", parse_dates=["date"])
    snaps = sorted(HIST.glob("board_*.csv"))
    names = pd.concat([bouts["fighter_a"], bouts["fighter_b"]]).dropna().unique().tolist()
    off = OfficialRanks(names)
    rated_path = PROC / "bouts_rated.csv"
    pred = {}
    if rated_path.exists():
        rr = pd.read_csv(rated_path)
        pred = dict(zip(rr["bout_url"], rr["p_a"]))
    rows = []
    for i, p in enumerate(snaps):
        t0 = pd.Timestamp(p.stem.split("_")[1])
        t1 = pd.Timestamp(snaps[i + 1].stem.split("_")[1]) if i + 1 < len(snaps) else pd.Timestamp.max
        board = pd.read_csv(p)
        pos = {(r.division, r.fighter): r.position for r in board.itertuples() if r.position <= board_size}
        window = bouts[(bouts["date"] > t0) & (bouts["date"] <= t1) & bouts["result_a"].isin([0.0, 1.0])]
        for x in window.itertuples():
            pa, pb = pos.get((x.division, x.fighter_a)), pos.get((x.division, x.fighter_b))
            if pa is None or pb is None or pa == pb:
                continue
            ours_right = (pa < pb) == (x.result_a == 1.0)
            oa, ob = off.rank(x.fighter_a, x.division, x.date), off.rank(x.fighter_b, x.division, x.date)
            off_right = None
            if oa is not None and ob is not None and oa != ob and max(oa, ob) < 99:
                off_right = (oa < ob) == (x.result_a == 1.0)
            rows.append({"snapshot": t0.date(), "date": x.date.date(), "division": x.division,
                         "fighter_a": x.fighter_a, "pos_a": pa, "fighter_b": x.fighter_b, "pos_b": pb,
                         "winner": x.fighter_a if x.result_a == 1.0 else x.fighter_b,
                         "ours_correct": ours_right, "official_a": oa, "official_b": ob, "official_correct": off_right,
                         "predictive_correct": (None if x.bout_url not in pred else (pred[x.bout_url] > 0.5) == (x.result_a == 1.0))})
    df = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "forward_validation.csv", index=False)
    both = df.dropna(subset=["official_correct"]) if not df.empty else df
    res = {
        "snapshots": len(snaps),
        "ranked_vs_ranked_bouts": int(len(df)),
        "ours_higher_ranked_win_rate": round(float(df["ours_correct"].mean()), 3) if len(df) else None,
        "same_bouts_official_also_ranked": int(len(both)),
        "ours_on_same_bouts": round(float(both["ours_correct"].mean()), 3) if len(both) else None,
        "official_on_same_bouts": round(float(both["official_correct"].astype(bool).mean()), 3) if len(both) else None,
        "predictive_elo_on_all_ranked_bouts": round(float(df["predictive_correct"].dropna().astype(bool).mean()), 3)
        if len(df) and df["predictive_correct"].notna().any() else None,
        "note": "Snapshots before the method freeze (v1.0) were rebuilt with today's rules, so they are an "
                "in-sample check; only bouts after the freeze date are a true forward test.",
    }
    (OUT / "forward_validation.json").write_text(json.dumps(res, indent=2, default=str))
    return res


if __name__ == "__main__":
    import sys
    if "--backfill" in sys.argv:
        months = int(sys.argv[sys.argv.index("--backfill") + 1]) if len(sys.argv) > sys.argv.index("--backfill") + 1 else 12
        print(len(backfill(months)), "snapshots")
    print(json.dumps(validate(), indent=2, default=str))
