"""
resume.py - Resume-first rating engine (who has earned it as of now).

Differences from the predictive Elo in elo.py:
  1. Decisions blend the judges' cards with the fight stats (card_weight = 0.5).
     Cards, per judge by point margin: 1 point (29-28, 48-47) = close, 0.6;
     2 points = 0.8; 3+ points (30-27, 49-46, 50-45) = 1.0; mean of three.
     Stats: logistic of the winner's dominance per minute. The official winner
     never scores below a draw, so a robbery (e.g. Jones-Reyes) earns the winner
     little and costs the loser little. Finishes score 1.0.
     "Dominant" needs the cards (2 of 3 at 3+ points) and the stats to agree.
  2. Loss protection, for losses to a division top-3 fighter or in a title fight:
       not dominant                      -> 15% of the normal drop
       dominant (2 of 3 cards 3+ points,
       or a round-one finish)            -> 75%
       round-one finish by a heavy
       favorite (>= 75% pre-fight)       -> 100%
     A loss right after another loss keeps at least 60% (streaks are not one-offs).
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
    protected_loss_mult: float = 0.15    # top-3 / title-fight loss that was not dominant
    dominant_loss_mult: float = 0.75     # top-3 / title-fight loss that was dominant
    heavy_favorite_p: float = 0.75       # winner's pre-fight win probability (about 3-1)
    consecutive_loss_mult: float = 0.6   # protection is weaker when the previous bout was also a loss
    no_card_decision_s: float = 0.75
    card_weight: float = 0.5             # decisions: share of the score from the judges; the rest from fight stats
    stat_scale: float = 2.0              # dominance per minute that maps to ~73% on the stats side
    dominant_stat_min: float = 0.0       # stats must not contradict the cards (winner not behind on stats)
    protect_top_n: int = 3
    quality_top_n: int = 7
    quality_min_wins: int = 5
    active_days: int = 540
    start: float = 1500.0

    def to_dict(self) -> dict:
        return asdict(self)


def judge_value(m: int) -> float:
    """Winner's score from one judge's point margin. 1 point (29-28, 48-47) is close,
    3+ points (30-27, 49-46, 50-45) is a clear, dominant round split."""
    return {3: 1.0, 2: 0.8, 1: 0.6, 0: 0.5, -1: 0.4, -2: 0.2}.get(max(-3, min(3, m)), 0.0 if m < 0 else 1.0)


def load_scorecards() -> pd.DataFrame:
    r = pd.read_csv(RAW / "ufc_fight_results.csv")
    r.columns = [c.strip() for c in r.columns]
    r = r[r["METHOD"].astype(str).str.strip().str.startswith("Decision")].copy()
    r["bout_url"] = r["URL"]
    r = r.drop_duplicates(subset="bout_url", keep="first")
    r["cards"] = r["DETAILS"].fillna("").astype(str).apply(_CARD.findall)

    def score(cards_raw):
        cards = [(int(a), int(b)) for a, b in cards_raw]
        if len(cards) != 3:
            return (np.nan, False, "")
        diffs = [a - b for a, b in cards]
        sign = np.sign(sum(np.sign(d) for d in diffs))   # the majority orientation is the winner
        if sign == 0:
            return (0.5, False, "")
        margins = [int(sign * d) for d in diffs]
        s_win = float(np.mean([judge_value(m) for m in margins]))
        dominant = sum(m >= 3 for m in margins) >= 2       # 2 of 3 cards at 49-46 / 30-27 or wider
        return (s_win, dominant, ",".join(str(m) for m in margins))

    out = r["cards"].apply(score)
    r["card_s"] = [o[0] for o in out]
    r["card_dominant"] = [o[1] for o in out]
    r["card_margins"] = [o[2] for o in out]
    return r[["bout_url", "card_s", "card_dominant", "card_margins"]]


def run_resume(bouts: pd.DataFrame, p: ResumeParams | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = p or ResumeParams()
    cards = load_scorecards()
    df = bouts.merge(cards, on="bout_url", how="left").sort_values(["date", "bout_id"]).reset_index(drop=True)

    rating: dict[str, float] = {}
    n_fights: dict[str, int] = {}
    wins: dict[str, int] = {}
    last_date: dict[str, pd.Timestamp] = {}
    last_div: dict[str, str] = {}
    last_result: dict[str, str] = {}
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
               "s_a": np.nan, "protected": "", "loss_mult": 1.0, "dominant": False,
               "decisive_loss": False, "quality_win": False}
        if pd.isna(res):
            rows.append({**rec, "r_post_a": ra, "r_post_b": rb})
            continue

        finish = row.method in ("KO/TKO", "SUB")
        if res == 0.5:
            s_win = 0.5
        elif finish:
            s_win = 1.0
        else:
            # decision: blend the judges with the fight stats, never below a draw for the official winner
            dom_w = row.dominance_a if res == 1.0 else -row.dominance_a
            stat_s = 1.0 / (1.0 + np.exp(-dom_w / p.stat_scale)) if not pd.isna(dom_w) else np.nan
            card_s = row.card_s
            if pd.isna(card_s) and pd.isna(stat_s):
                s_win = p.no_card_decision_s
            elif pd.isna(card_s):
                s_win = stat_s
            elif pd.isna(stat_s):
                s_win = float(card_s)
            else:
                s_win = p.card_weight * float(card_s) + (1 - p.card_weight) * stat_s
            s_win = float(np.clip(s_win, 0.5, 1.0))
        sa = s_win if res == 1.0 else (1 - s_win if res == 0.0 else 0.5)

        ka = p.k * (p.k_new_mult if n_fights.get(a, 0) < p.n_new else 1.0)
        kb = p.k * (p.k_new_mult if n_fights.get(b, 0) < p.n_new else 1.0)
        da, db = ka * (sa - ea), kb * ((1 - sa) - (1 - ea))

        # how the loss is treated
        r1_finish = finish and row.round == 1
        dom_winner = (row.dominance_a if res == 1.0 else -row.dominance_a) if res in (0.0, 1.0) else np.nan
        stats_agree = pd.isna(dom_winner) or dom_winner >= p.dominant_stat_min
        dominant = bool(r1_finish or (not finish and row.card_dominant is True and stats_agree))
        rec["s_win"] = s_win if res in (0.0, 1.0) else np.nan
        rec["dominant"] = dominant if res in (0.0, 1.0) else False
        if res in (0.0, 1.0):
            loser = "a" if res == 0.0 else "b"
            winner_pos = pos_b if loser == "a" else pos_a
            p_winner = (1 - ea) if loser == "a" else ea
            protected_ctx = bool(row.title_fight) or winner_pos <= p.protect_top_n
            if protected_ctx:
                if r1_finish and p_winner >= p.heavy_favorite_p:
                    mult = 1.0                    # the real gap: a heavy favorite finished it in round one
                elif dominant:
                    mult = p.dominant_loss_mult
                else:
                    mult = p.protected_loss_mult
                    loser_name = a if loser == "a" else b
                    if last_result.get(loser_name) == "L":
                        mult = max(mult, p.consecutive_loss_mult)   # a losing streak is not a one-off
                if loser == "a" and da < 0:
                    da *= mult
                if loser == "b" and db < 0:
                    db *= mult
                rec["protected"] = loser
                rec["loss_mult"] = mult
            rec["decisive_loss"] = dominant

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
            last_result[f] = "W" if won else ("L" if res in (0.0, 1.0) else "D")
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
