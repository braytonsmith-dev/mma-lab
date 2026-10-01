"""
sensitivity.py - What each hand-set constant of the REAL resume engine costs or buys out of sample.

The engine's constants encode stated ranking principles (what a resume should reward and forgive);
they are not fitted. This sweep changes one constant at a time from the v1.0 values, reruns the
chronological engine, and scores the pre-fight resume rating as a forecaster on the same 3,390
held-out bouts (2020-2026) the prediction model is graded on. Lower log loss is better; the
v1.0 row is the reference. It answers "what does this principle cost in predictive accuracy",
not "which value is right": the resume board is judged on its own pre-registered protocol.

Writes outputs/constants_sensitivity.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from mmalab.resume import ResumeParams, run_resume

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
TEST_FROM = "2020-01-01"

SWEEP = {
    "k": [30, 45, 60, 80, 100],
    "k_new_mult": [1.0, 1.5, 2.0],
    "protected_loss_mult": [0.0, 0.15, 0.3, 0.5, 1.0],
    "dominant_loss_mult": [0.5, 0.75, 1.0],
    "consecutive_loss_mult": [0.15, 0.6, 1.0],
    "heavy_favorite_p": [0.6, 0.75, 0.9, 1.01],
    "card_weight": [0.0, 0.25, 0.5, 0.75, 1.0],
    "stat_scale": [1.0, 2.0, 3.0],
    "close_s": [0.6, 0.7, 0.8],
    "proof_gain": [0.0, 0.1, 0.2],
    "proof_top_n": [3, 5, 7],
    "protect_top_n": [1, 3, 5],
    "upset_quick_finish_mult": [0.5, 0.7, 1.0],
}
PRINCIPLE = {
    "k": "rating speed; 60 sits between chess (20 to 40) and Fight Matrix (170)",
    "k_new_mult": "newcomers converge faster (FIDE practice), first n_new = 5 bouts",
    "protected_loss_mult": "a non-dominant loss in a title fight or to a top-3 fighter counts for little",
    "dominant_loss_mult": "a dominant loss in that context still costs most of its value",
    "consecutive_loss_mult": "protection weakens on a second straight loss",
    "heavy_favorite_p": "a round-one finish by a favorite at or above this probability costs full value (1.01 = never)",
    "card_weight": "decisions: share of the result taken from the judges' cards, the rest from fight statistics",
    "stat_scale": "dominance per minute that maps to about 73% of a performance win",
    "close_s": "a decision at or below this blended score counts as close (29-28 territory)",
    "proof_gain": "close loss to a top-5 fighter by someone outside the top 5 gains this share of K",
    "proof_top_n": "the rank that defines an elite opponent for proof of concept",
    "protect_top_n": "the rank at or above which an opponent's win is a protected context",
    "upset_quick_finish_mult": "a round-one upset finish moves both fighters by this share",
}


def score(out: pd.DataFrame, keep: set) -> dict:
    m = out[out["bout_id"].isin(keep)]
    y = m["result_a"].to_numpy(dtype=float)
    p = 1 / (1 + 10 ** ((m["r_pre_b"] - m["r_pre_a"]) / 400))
    p = np.clip(p.to_numpy(), 1e-6, 1 - 1e-6)
    return {"n": int(len(m)), "log_loss": round(float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), 4),
            "brier": round(float(np.mean((p - y) ** 2)), 4), "accuracy": round(float(np.mean((p > 0.5) == (y == 1))), 4)}


def main() -> None:
    base = yaml.safe_load((ROOT / "config" / "weights.yaml").read_text())["resume"]["engine"]
    bouts = pd.read_csv(PROC / "bouts_with_stats.csv", parse_dates=["date"])
    keep = set(bouts.loc[(bouts["date"] >= TEST_FROM) & bouts["result_a"].isin([0.0, 1.0]), "bout_id"])
    rows = []
    ref = score(run_resume(bouts, ResumeParams(**base))[0], keep)
    rows.append({"constant": "v1.0 reference", "value": "", "principle": "all constants at their configured values", **ref,
                 "delta_log_loss_vs_v1": 0.0})
    for name, values in SWEEP.items():
        for v in values:
            if v == base.get(name):
                continue
            params = {**base, name: v}
            r = score(run_resume(bouts, ResumeParams(**params))[0], keep)
            rows.append({"constant": name, "value": v, "principle": PRINCIPLE[name], **r,
                         "delta_log_loss_vs_v1": round(r["log_loss"] - ref["log_loss"], 4)})
            print(name, v, r)
    # the principles switched off together: a plain resume Elo on cards and stats
    off = {**base, "protected_loss_mult": 1.0, "dominant_loss_mult": 1.0, "consecutive_loss_mult": 1.0,
           "proof_gain": 0.0, "upset_quick_finish_mult": 1.0, "heavy_favorite_p": 1.01}
    r = score(run_resume(bouts, ResumeParams(**off))[0], keep)
    rows.append({"constant": "all loss protections off", "value": "", "principle": "plain Elo on cards and stats, every loss at full cost",
                 **r, "delta_log_loss_vs_v1": round(r["log_loss"] - ref["log_loss"], 4)})
    df = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "constants_sensitivity.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
