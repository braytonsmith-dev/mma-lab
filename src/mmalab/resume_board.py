"""
resume_board.py - The divisional boards (Option B): who has earned it, as of now.

score = 0.70 * rating + 0.30 * quality wins, each scaled within the division by
its interdecile range: (x - median) / (90th pct - 10th pct). Distances are kept,
so a 70-point rating gap counts more than a 5-point one (percentiles would not).

  rating         resume rating from resume.py (judges + stats, loss protection),
                 minus an inactivity penalty after 12 months unless the layoff is a
                 documented injury (config/layoffs.yaml)
  quality wins   wins over UFC fighters with 5+ UFC wins or ranked top 7 at the
                 time, weighted by age (<=3 yrs 1.0, 3-5 0.6, 5-10 0.3, 10-15 0.1);
                 each dominant loss in the last 3 years cancels one quality win
  head-to-head   if a fighter beat someone in their most recent meeting (last 3
                 years) and sits at most 3 spots below him, he moves directly above

Display-only: last five (W-L), streak, entrenched (5+ quality wins in 15 years),
danger-adjusted durability (KO/TKO losses weighted by how dangerous the opponent was).

Writes outputs/composite_rankings_full.csv (same columns publish.py and
compare.py read), composite_top15_by_division.csv and composite_boards.md.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from mmalab.resume import ResumeParams, run_resume
from mmalab.rankings import RANKED_DIVISIONS, champions

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
CFG = ROOT / "config"


def _yaml(name: str) -> dict:
    p = CFG / name
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def horizon_weight(age_years: float, horizons: dict) -> float:
    for limit in sorted(horizons):
        if age_years <= float(limit):
            return float(horizons[limit])
    return 0.0


def idr_scale(s: pd.Series) -> pd.Series:
    q10, q50, q90 = s.quantile([0.1, 0.5, 0.9])
    return (s - q50) / max(q90 - q10, 1e-9)


def last_five(out: pd.DataFrame) -> pd.DataFrame:
    rows = []
    d = out[out["result_a"].isin([0.0, 1.0])]
    long = pd.concat([
        pd.DataFrame({"fighter": d["fighter_a"], "date": d["date"], "bout_id": d["bout_id"], "w": d["result_a"] == 1.0}),
        pd.DataFrame({"fighter": d["fighter_b"], "date": d["date"], "bout_id": d["bout_id"], "w": d["result_a"] == 0.0}),
    ]).sort_values(["date", "bout_id"])
    for f, g in long.groupby("fighter"):
        seq = ["W" if x else "L" for x in g["w"]]
        last = seq[-5:]
        streak = 1
        for r in reversed(seq[:-1]):
            if r != seq[-1]:
                break
            streak += 1
        rows.append((f, f"{last.count('W')}-{last.count('L')}", f"{seq[-1]}{streak}"))
    return pd.DataFrame(rows, columns=["fighter", "last5", "streak"]).set_index("fighter")


def durability(out: pd.DataFrame, as_of: pd.Timestamp, years: int = 10) -> pd.Series:
    """KO/TKO losses per UFC bout, each weighted by 1 - opponent danger.
    danger = 0.5 * min(opponent prior KO-win rate / 0.5, 1) + 0.5 * rank factor at fight time."""
    o = out.sort_values(["date", "bout_id"])
    ko_w, n = {}, {}
    pen, bouts = {}, {}
    for x in o.itertuples():
        a, b = x.fighter_a, x.fighter_b
        recent = (as_of - x.date).days / 365.25 <= years
        if recent:
            for f in (a, b):
                bouts[f] = bouts.get(f, 0) + 1
            if x.method == "KO/TKO" and x.result_a in (0.0, 1.0):
                w, l = (a, b) if x.result_a == 1.0 else (b, a)
                wpos = x.pos_a if w == a else x.pos_b
                power = (ko_w.get(w, 0) + 1) / (n.get(w, 0) + 2)
                elite = 1.0 if wpos <= 3 else 0.7 if wpos <= 7 else 0.4 if wpos <= 15 else 0.15
                danger = 0.5 * min(power / 0.5, 1.0) + 0.5 * elite
                pen[l] = pen.get(l, 0.0) + (1 - danger)
        for f, won in ((a, x.result_a == 1.0), (b, x.result_a == 0.0)):
            n[f] = n.get(f, 0) + 1
            if won and x.method == "KO/TKO":
                ko_w[f] = ko_w.get(f, 0) + 1
    return pd.Series({f: pen.get(f, 0.0) / c for f, c in bouts.items()}, name="ko_risk")


def head_to_head(board: pd.DataFrame, out: pd.DataFrame, as_of: pd.Timestamp, max_gap: int, max_years: float,
                 max_gap_recent: int | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Winner of the most recent meeting (within max_years) moves directly above the loser
    when he is ranked no more than max_gap spots below. Most recent meetings are applied last."""
    notes = []
    max_gap_recent = max_gap_recent or max_gap
    d = out[out["result_a"].isin([0.0, 1.0]) & ((as_of - out["date"]).dt.days <= max_years * 365.25)]
    d = d.sort_values("date")
    last_meeting = {}
    for x in d.itertuples():
        key = tuple(sorted((x.fighter_a, x.fighter_b)))
        last_meeting[key] = (x.date, x.fighter_a if x.result_a == 1.0 else x.fighter_b)
    fixed = []
    for div, g in board.groupby("division"):
        order = list(g.sort_values("pos")["fighter"])
        for (f1, f2), (date, winner) in sorted(last_meeting.items(), key=lambda kv: kv[1][0]):
            if f1 in order and f2 in order:
                loser = f2 if winner == f1 else f1
                iw, il = order.index(winner), order.index(loser)
                gap_allowed = max_gap_recent if (as_of - date).days <= 365 else max_gap
                if 0 < iw - il <= gap_allowed:
                    order.insert(il, order.pop(iw))
                    notes.append(f"{div}: {winner} moved above {loser} (won {date.date()})")
        fixed.append(pd.DataFrame({"division": div, "fighter": order, "pos": range(1, len(order) + 1)}))
    fixed = pd.concat(fixed)
    return board.drop(columns=["pos"]).merge(fixed, on=["division", "fighter"]), notes


def build(as_of: str | None = None, weights: dict | None = None, stability: bool = True) -> tuple[pd.DataFrame, dict]:
    cfg = yaml.safe_load((CFG / "weights.yaml").read_text())
    rc = cfg["resume"]
    w = weights or rc["weights"]
    bouts = pd.read_csv(PROC / "bouts_with_stats.csv", parse_dates=["date"])
    as_of_ts = pd.Timestamp(as_of) if as_of else bouts["date"].max() + pd.Timedelta(days=1)
    bouts = bouts[bouts["date"] < as_of_ts]
    out, hist = run_resume(bouts, ResumeParams(**rc["engine"]))

    injured = _yaml("layoffs.yaml")
    gone = _yaml("roster_exclusions.yaml")
    inact = rc["inactivity"]

    last = hist.groupby("fighter").tail(1).set_index("fighter")
    ranked_hist = hist[hist["division"].isin(RANKED_DIVISIONS)]
    div_latest = ranked_hist.groupby("fighter").tail(1).set_index("fighter")["division"]
    f = pd.DataFrame({"rating_raw": last["rating"], "last_fight": last["date"]})
    f["division"] = div_latest.reindex(f.index)
    # last appearance includes no-contests
    appear = pd.concat([out[["date", "fighter_a"]].rename(columns={"fighter_a": "fighter"}),
                        out[["date", "fighter_b"]].rename(columns={"fighter_b": "fighter"})]).groupby("fighter")["date"].max()
    f["days_since"] = (as_of_ts - appear.reindex(f.index)).dt.days
    f["injury"] = f.index.isin(set(injured))
    max_days = np.where(f["injury"], inact["injury_max_days"], inact["max_days"])
    f = f[(f["days_since"] <= max_days) & f["division"].isin(RANKED_DIVISIONS) & ~f.index.isin(set(gone))].copy()
    over = ((f["days_since"] - inact["grace_days"]) / (inact["max_days"] - inact["grace_days"])).clip(0, 1)
    f["inactivity_penalty"] = np.where(f["injury"], 0.0, over * inact["max_penalty_points"])
    f["rating"] = f["rating_raw"] - f["inactivity_penalty"]

    # quality wins net of dominant losses, horizon weighted
    d = out[out["result_a"].isin([0.0, 1.0])].copy()
    d["winner"] = np.where(d["result_a"] == 1.0, d["fighter_a"], d["fighter_b"])
    d["loser"] = np.where(d["result_a"] == 1.0, d["fighter_b"], d["fighter_a"])
    d["age"] = (as_of_ts - d["date"]).dt.days / 365.25
    hz = {float(k): v for k, v in rc["horizons"].items()}
    d["hw"] = d["age"].apply(lambda a: horizon_weight(a, hz))
    qw = d[d["quality_win"]].groupby("winner")["hw"].sum()
    # a blowout loss says the gap is real now: only dominant losses in the last 3 years cancel wins
    dl = d[d["decisive_loss"] & (d["age"] <= rc.get("decisive_loss_years", 3))].groupby("loser")["hw"].sum()
    q15 = d[d["quality_win"] & (d["age"] <= 15)].groupby("winner").size()
    f["quality_wins"] = (qw.reindex(f.index).fillna(0) - dl.reindex(f.index).fillna(0)).clip(lower=0)
    if rc.get("declining_guard", False):
        # a negative last five means older wins (3+ years) stop propping the fighter up
        recent_qw = d[d["quality_win"] & (d["age"] <= 3)].groupby("winner")["hw"].sum()
        lf = last_five(out)
        neg = lf["last5"].apply(lambda r: int(r.split("-")[1]) > int(r.split("-")[0]))
        declining = set(neg[neg].index)
        mask = f.index.isin(declining)
        f.loc[mask, "quality_wins"] = (recent_qw.reindex(f.index[mask]).fillna(0)
                                       - dl.reindex(f.index[mask]).fillna(0)).clip(lower=0).values
    f["quality_wins_15y"] = q15.reindex(f.index).fillna(0).astype(int)
    f["entrenched"] = f["quality_wins_15y"] >= 5
    ufc_bouts = pd.concat([out["fighter_a"], out["fighter_b"]]).value_counts()
    f["ufc_bouts"] = ufc_bouts.reindex(f.index).fillna(0).astype(int)
    f = f.join(last_five(out)).join(durability(out, as_of_ts))
    f = f.reset_index().rename(columns={"index": "fighter"})

    champs = champions(out, as_of_ts)
    interim = _yaml("interim_champions.yaml")
    f["champion"] = f.apply(lambda r: champs.get(r["division"]) == r["fighter"], axis=1)
    f["interim"] = f.apply(lambda r: interim.get(r["division"]) == r["fighter"], axis=1)

    def score(frame: pd.DataFrame, wts: dict) -> pd.DataFrame:
        parts = []
        for div, g in frame.groupby("division"):
            g = g.copy()
            g["score"] = wts["rating"] * idr_scale(g["rating"]) + wts["quality_wins"] * idr_scale(g["quality_wins"])
            cont = g[~g["champion"] & ~g["interim"]].sort_values("score", ascending=False)
            g["pos"] = np.nan
            g.loc[cont.index, "pos"] = range(1, len(cont) + 1)
            parts.append(g)
        return pd.concat(parts)

    board = score(f, w)
    titled = board[board["pos"].isna()].copy()
    cont = board[board["pos"].notna()].copy()
    h2h = rc["head_to_head"]
    cont, h2h_notes = head_to_head(cont, out, as_of_ts, h2h["max_gap"], h2h["max_years"],
                                   h2h.get("max_gap_recent"))

    # stability: interdecile range of position across weight vectors near the chosen weights
    if stability:
        rng = np.random.default_rng(7)
        keys = list(w)
        base = np.array([w[k] for k in keys])
        draws = []
        for _ in range(rc["stability_draws"]):
            wv = dict(zip(keys, rng.dirichlet(base * rc["stability_concentration"])))
            s = score(f, wv)
            draws.append(s[s["pos"].notna()][["division", "fighter", "pos"]])
        dd = pd.concat(draws).groupby(["division", "fighter"])["pos"].quantile([0.1, 0.9]).unstack()
        dd.columns = ["rank_p10", "rank_p90"]
        cont = cont.merge(dd.reset_index(), on=["division", "fighter"], how="left")
    else:
        cont["rank_p10"] = cont["rank_p90"] = cont["pos"]
    titled["rank_p10"] = titled["rank_p90"] = 0
    board = pd.concat([titled, cont], ignore_index=True)
    board["rank"] = board["pos"].fillna(0).astype(int)
    board = board.sort_values(["division", "rank", "interim"], ascending=[True, True, True])

    # columns expected by publish.py / compare.py
    board["record_3y"] = board["last5"]
    board["top15_wins"] = board["quality_wins_15y"]
    meta = {"as_of": as_of_ts - pd.Timedelta(days=1), "weights": w, "h2h": h2h_notes, "champs": champs,
            "interim": interim}
    return board, meta


def main(as_of: str | None = None) -> None:
    cfg = yaml.safe_load((CFG / "weights.yaml").read_text())
    board, meta = build(as_of)
    OUT.mkdir(exist_ok=True)
    board.to_csv(OUT / "composite_rankings_full.csv", index=False)
    size = cfg["board_size"]
    top = board[board["rank"] <= size]
    cols = ["division", "rank", "fighter", "champion", "interim", "score", "rating", "quality_wins",
            "quality_wins_15y", "entrenched", "last5", "streak", "days_since", "injury", "ko_risk",
            "rank_p10", "rank_p90"]
    top[cols].round(3).to_csv(OUT / "composite_top15_by_division.csv", index=False)

    lines = [f"# Divisional boards as of {meta['as_of'].date()}",
             f"weights: {meta['weights']}; stability = 10th-90th percentile position across nearby weights", ""]
    for div in RANKED_DIVISIONS:
        g = top[top["division"] == div]
        if g.empty:
            continue
        lines.append(f"\n## {div}" + ("   (title vacant)" if div not in meta["champs"] and div not in meta["interim"] else ""))
        for r in g.itertuples():
            label = " C" if r.champion else ("IC" if r.interim else f"{r.rank:>2}")
            inj = " (injury layoff)" if r.injury else ""
            lines.append(f"{label}. {r.fighter:<26} score {r.score:+.2f}  rating {r.rating:6.0f}  last5 {r.last5:<4} "
                         f"QW {r.quality_wins:4.1f} ({int(r.quality_wins_15y)} in 15y{' E' if r.entrenched else ''})  "
                         f"days {int(r.days_since):>3}{inj}  band [{int(r.rank_p10)}-{int(r.rank_p90)}]")
    lines += ["", "## Head-to-head moves applied"] + [f"- {n}" for n in meta["h2h"]]
    (OUT / "composite_boards.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
