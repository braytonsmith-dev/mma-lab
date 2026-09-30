"""
resume.py - Resume-first rating engine (who has earned it as of now).

Differences from the predictive Elo in elo.py:
  1. Decisions are scored from the judges' cards, not strike stats.
     Per judge, round share = 0.5 + margin / (2 * rounds): 30-27 or 50-45 -> 1.0,
     49-46 -> 0.8, 29-28 -> 0.67, 48-47 -> 0.6. The winner's score is
     win_base + (1 - win_base) * (share - 0.5) / 0.5, so a 49-46 sweep of the
     cards is a clear win, not a near-draw. Finishes score 1.0.
  2. Loss protection: a loss to a fighter inside the division's top 3 at fight
     time, or in a title fight, moves the loser's rating by only
     `protected_loss_mult` of the normal amount, unless the loss was dominant
     (every card at least 49-46 / 30-27, or a first-round finish).
  3. No rating decay for layoffs. Inactivity is handled separately, with an
     injury exemption (config/layoffs.yaml).
  4. Records quality wins as they happen: opponent had >= 5 UFC wins, or was
     inside the division top 7 at fight time. Five or more = "entrenched".

Positions at fight time are computed from this same rating among fighters
active in the prior `active_days` in that division.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

_CARD = re.compile(r"(\d+)\s*-\s*(\d+)")
EVENT_ALIASES = {
    "UFC Fight Night: Grasso vs. Shevchenko 2": "Noche UFC: Grasso vs. Shevchenko 2",
    "UFC Fight Night: Lopes vs. Silva": "Noche UFC: Lopes vs. Silva",
}


@dataclass
class ResumeParams:
    k: float = 60.0
    k_new_mult: float = 1.5
    n_new: int = 5
    win_base: float = 0.6            # score for a 50/50-on-the-cards win; 1.0 for a sweep or finish
    protected_loss_mult: float = 0.15
    protect_top_n: int = 3
    quality_top_n: int = 7
    quality_min_wins: int = 5
    active_days: int = 540
    start: float = 1500.0

    def to_dict(self) -> dict:
        return asdict(self)


def load_scorecards() -> pd.DataFrame:
    r = pd.read_csv(RAW / "ufc_fight_results.csv")
    r.columns = [c.strip() for c in r.columns]
    r = r[r["METHOD"].astype(str).str.strip().str.startswith("Decision")].copy()
    r["bout_url"] = r["URL"]
    r = r.drop_duplicates(subset="bout_url", keep="first")
    r["cards"] = r["DETAILS"].fillna("").astype(str).apply(_CARD.findall)
    r["rounds"] = pd.to_numeric(r["ROUND"], errors="coerce")

    def winner_shares(row) -> float | None:
        cards = [(int(a), int(b)) for a, b in row["cards"]]
        if len(cards) != 3 or not row["rounds"]:
            return None
        diffs = [a - b for a, b in cards]
        sign = np.sign(sum(np.sign(d) for d in diffs))    # majority orientation = the winner
        if sign == 0:
            return 0.5
        R = row["rounds"]
        shares = [min(1.0, max(0.0, 0.5 + sign * d / (2 * R))) for d in diffs]
        return float(np.mean(shares)), float(min(shares))

    out = r.apply(winner_shares, axis=1)
    r["card_share_mean"] = [o[0] if isinstance(o, tuple) else np.nan for o in out]
    r["card_share_min"] = [o[1] if isinstance(o, tuple) else np.nan for o in out]
    return r[["bout_url", "card_share_mean", "card_share_min", "cards"]]


def run_resume(bouts: pd.DataFrame, p: ResumeParams | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = p or ResumeParams()
    cards = load_scorecards()
    df = bouts.merge(cards, on="bout_url", how="left").sort_values(["date", "bout_id"]).reset_index(drop=True)

    rating: dict[str, float] = {}
    n_fights: dict[str, int] = {}
    wins: dict[str, int] = {}
    last_date: dict[str, pd.Timestamp] = {}
    last_div: dict[str, str] = {}
    active_days = pd.Timedelta(days=p.active_days)

    # per-division index keeps position() cheap
    div_members: dict[str, set] = {}

    def position_fast(name: str, div: str, date: pd.Timestamp) -> int:
        r0 = rating.get(name, p.start)
        better = 0
        for f in div_members.get(div, ()):
            if f != name and date - last_date[f] <= active_days and rating[f] > r0:
                better += 1
        return better + 1

    rows, hist = [], []
    for row in df.itertuples(index=False):
        a, b, d, div = row.fighter_a, row.fighter_b, row.date, row.division
        ra, rb = rating.get(a, p.start), rating.get(b, p.start)
        pos_a = position_fast(a, div, d) if a in rating else 999
        pos_b = position_fast(b, div, d) if b in rating else 999
        ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        res = row.result_a
        rec = {"bout_id": row.bout_id, "pos_a": pos_a, "pos_b": pos_b, "r_pre_a": ra, "r_pre_b": rb,
               "wins_pre_a": wins.get(a, 0), "wins_pre_b": wins.get(b, 0),
               "s_a": np.nan, "protected": "", "quality_win": False}
        if pd.isna(res):
            rows.append({**rec, "r_post_a": ra, "r_post_b": rb})
            continue

        finish = row.method in ("KO/TKO", "SUB")
        share = row.card_share_mean
        if res == 0.5:
            s_win = 0.5
        elif finish or pd.isna(share):
            s_win = 1.0
        else:
            s_win = p.win_base + (1 - p.win_base) * (share - 0.5) / 0.5
            s_win = float(np.clip(s_win, 0.5, 1.0))
        sa = s_win if res == 1.0 else (1 - s_win if res == 0.0 else 0.5)

        ka = p.k * (p.k_new_mult if n_fights.get(a, 0) < p.n_new else 1.0)
        kb = p.k * (p.k_new_mult if n_fights.get(b, 0) < p.n_new else 1.0)
        da, db = ka * (sa - ea), kb * ((1 - sa) - (1 - ea))

        # loss protection
        dominant = (finish and row.round == 1) or (
            not finish and not pd.isna(row.card_share_min) and row.card_share_min >= 0.8)
        if res in (0.0, 1.0) and not dominant:
            loser, winner_pos = ("a", pos_b) if res == 0.0 else ("b", pos_a)
            if row.title_fight or winner_pos <= p.protect_top_n:
                if loser == "a" and da < 0:
                    da *= p.protected_loss_mult
                    rec["protected"] = "a"
                if loser == "b" and db < 0:
                    db *= p.protected_loss_mult
                    rec["protected"] = "b"

        # quality win bookkeeping (opponent strength measured before the bout)
        if res == 1.0:
            rec["quality_win"] = wins.get(b, 0) >= p.quality_min_wins or pos_b <= p.quality_top_n
        elif res == 0.0:
            rec["quality_win"] = wins.get(a, 0) >= p.quality_min_wins or pos_a <= p.quality_top_n

        na, nb = ra + da, rb + db
        rating[a], rating[b] = na, nb
        for f, won in ((a, res == 1.0), (b, res == 0.0)):
            n_fights[f] = n_fights.get(f, 0) + 1
            wins[f] = wins.get(f, 0) + int(won)
            if last_div.get(f) != div and f in last_div:
                div_members.get(last_div[f], set()).discard(f)
            last_div[f], last_date[f] = div, d
            div_members.setdefault(div, set()).add(f)
        rec.update({"s_a": sa, "r_post_a": na, "r_post_b": nb})
        rows.append(rec)
        hist.append((a, d, row.bout_id, div, na))
        hist.append((b, d, row.bout_id, div, nb))

    out = df.merge(pd.DataFrame(rows), on="bout_id", how="left")
    h = pd.DataFrame(hist, columns=["fighter", "date", "bout_id", "division", "rating"])
    return out, h
