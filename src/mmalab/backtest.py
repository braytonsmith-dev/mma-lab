"""
backtest.py - Out-of-sample evaluation of the Elo engine.

Protocol
  1. Warm-up:  1994-2009 ratings accumulate, never scored.
  2. Tuning:   2010-2019 bouts are scored while grid-searching EloParams.
  3. Test:     2020-2026 bouts are scored once with the tuned parameters.
     Nothing in the test window influenced the parameter choice.
  4. Market:   on bouts with closing odds (BestFightOdds, Nov 2014 - Dec 2023)
     compare Elo against the de-vigged market probability on the same bouts.

Metrics: log loss (primary), Brier score, accuracy. Coin flip log loss = 0.6931.
"""
from __future__ import annotations

import itertools
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from mmalab.elo import EloParams, run_elo

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"

TUNE = (pd.Timestamp("2010-01-01"), pd.Timestamp("2019-12-31"))
TEST = (pd.Timestamp("2020-01-01"), pd.Timestamp("2026-12-31"))


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    brier = np.mean((p - y) ** 2)
    acc = np.mean((p > 0.5) == (y > 0.5))
    return {"n": int(len(y)), "log_loss": round(float(ll), 4),
            "brier": round(float(brier), 4), "accuracy": round(float(acc), 4)}


def scored(df: pd.DataFrame, window: tuple) -> pd.DataFrame:
    m = df["date"].between(*window) & df["result_a"].isin([0.0, 1.0])
    return df[m]


def evaluate(bouts: pd.DataFrame, params: EloParams, window: tuple) -> dict:
    rated, _ = run_elo(bouts, params)
    s = scored(rated, window)
    return metrics(s["result_a"].to_numpy(), s["p_a"].to_numpy())


def grid_search(bouts: pd.DataFrame) -> tuple[EloParams, pd.DataFrame]:
    """Two families share one grid: classic (mov_weight = 0) and
    performance-adjusted (mov_weight > 0, with optional win/finish floors)."""
    common = {"k": [40, 60, 80, 100, 130], "k_new_mult": [1.5, 2.0],
              "split_mult": [0.8], "layoff_regress_per_year": [0.0, 0.25]}
    classic = {**common, "finish_mult": [1.0, 1.25], "mov_weight": [0.0], "mov_scale": [3.0],
               "win_floor": [0.0], "finish_floor": [0.0]}
    mov = {**common, "finish_mult": [1.0], "mov_weight": [0.5, 0.75, 0.9], "mov_scale": [2.0, 3.0],
           "win_floor": [0.0, 0.5], "finish_floor": [0.0, 0.75]}
    rows = []
    for grid in (classic, mov):
        keys = list(grid)
        for combo in itertools.product(*grid.values()):
            kw = dict(zip(keys, combo))
            m = evaluate(bouts, EloParams(**kw), TUNE)
            rows.append({**kw, **m})
    res = pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)
    keys = list(mov)
    best = res.iloc[0]
    best_params = EloParams(**{k: float(best[k]) for k in keys})
    return best_params, res


# ---------- market comparison ----------

def _norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z ]", "", s.lower())
    return " ".join(s.split())


def market_comparison(rated: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    odds = pd.read_csv(ROOT / "data" / "raw" / "odds_bestfightodds_2014_2023.csv")
    odds["date"] = pd.to_datetime(odds["date"])
    odds = odds.replace([np.inf, -np.inf], np.nan).dropna(subset=["favourite_odds", "underdog_odds"])
    odds = odds[(odds["favourite_odds"] > 1.0) & (odds["underdog_odds"] > 1.0)]
    odds["fav_n"] = odds["favourite"].map(_norm)
    odds["dog_n"] = odds["underdog"].map(_norm)
    # de-vig: normalise implied probabilities so they sum to one
    inv_f, inv_d = 1 / odds["favourite_odds"], 1 / odds["underdog_odds"]
    odds["p_fav_market"] = inv_f / (inv_f + inv_d)

    r = rated.copy()
    r["a_n"] = r["fighter_a"].map(_norm)
    r["b_n"] = r["fighter_b"].map(_norm)

    # match on date and the unordered pair of names
    r["key"] = r.apply(lambda x: (x["date"].date(), tuple(sorted([x["a_n"], x["b_n"]]))), axis=1)
    odds["key"] = odds.apply(lambda x: (x["date"].date(), tuple(sorted([x["fav_n"], x["dog_n"]]))), axis=1)
    m = r.merge(odds[["key", "fav_n", "p_fav_market", "favourite_odds", "underdog_odds"]], on="key", how="inner")
    m = m[m["result_a"].isin([0.0, 1.0])].copy()
    # market probability expressed for fighter_a
    m["p_a_market"] = np.where(m["a_n"] == m["fav_n"], m["p_fav_market"], 1 - m["p_fav_market"])
    m["p_a_blend"] = 0.5 * m["p_a"] + 0.5 * m["p_a_market"]

    y = m["result_a"].to_numpy()
    out = {
        "matched_bouts": int(len(m)),
        "date_range": [str(m["date"].min().date()), str(m["date"].max().date())],
        "elo": metrics(y, m["p_a"].to_numpy()),
        "market_devigged": metrics(y, m["p_a_market"].to_numpy()),
        "blend_50_50": metrics(y, m["p_a_blend"].to_numpy()),
        "coin_flip_log_loss": 0.6931,
    }
    return out, m


def calibration(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    s = df.copy()
    s["bin"] = pd.cut(s["p_a"], np.linspace(0, 1, bins + 1), include_lowest=True)
    g = s.groupby("bin", observed=True).agg(n=("result_a", "size"),
                                            predicted=("p_a", "mean"),
                                            actual=("result_a", "mean")).reset_index()
    g["bin"] = g["bin"].astype(str)
    return g


def main() -> None:
    OUT.mkdir(exist_ok=True)
    bouts = pd.read_csv(PROC / "bouts_with_stats.csv", parse_dates=["date"])

    baseline = EloParams(k=32, k_new_mult=1.0, finish_mult=1.0, split_mult=1.0, layoff_regress_per_year=0.0)
    base_tune = evaluate(bouts, baseline, TUNE)
    base_test = evaluate(bouts, baseline, TEST)

    best, grid = grid_search(bouts)
    grid.to_csv(OUT / "elo_grid_search.csv", index=False)
    tuned_tune = evaluate(bouts, best, TUNE)
    tuned_test = evaluate(bouts, best, TEST)

    # ablation: best classic (results-only) model from the same grid
    keys = [c for c in grid.columns if c not in ("n", "log_loss", "brier", "accuracy")]
    cb = grid[grid["mov_weight"] == 0.0].iloc[0]
    classic_best = EloParams(**{k: float(cb[k]) for k in keys})
    classic_tune = evaluate(bouts, classic_best, TUNE)
    classic_test = evaluate(bouts, classic_best, TEST)

    # the interpretable model used for the public boards (config/weights.yaml -> elo)
    import yaml
    ranking_model = EloParams(**yaml.safe_load((ROOT / "config" / "weights.yaml").read_text())["elo"])
    ranking_tune = evaluate(bouts, ranking_model, TUNE)
    ranking_test = evaluate(bouts, ranking_model, TEST)

    rated, hist = run_elo(bouts, best)
    rated.to_csv(PROC / "bouts_rated.csv", index=False)
    hist.to_csv(PROC / "elo_history.csv", index=False)

    mkt, matched = market_comparison(rated)
    matched.to_csv(OUT / "market_matched_bouts.csv", index=False)
    calibration(scored(rated, TEST)).to_csv(OUT / "calibration_test_2020_2026.csv", index=False)

    # year-by-year test performance
    s = scored(rated, (pd.Timestamp("2015-01-01"), TEST[1]))
    by_year = s.groupby(s["date"].dt.year).apply(
        lambda g: pd.Series(metrics(g["result_a"].to_numpy(), g["p_a"].to_numpy()))).reset_index()
    by_year.to_csv(OUT / "elo_by_year.csv", index=False)

    report = {
        "protocol": {"warmup": "1994-2009", "tune": "2010-2019", "test": "2020-2026 (through last scraped event)"},
        "baseline_params": baseline.to_dict(),
        "baseline_tune": base_tune, "baseline_test": base_test,
        "classic_tuned_params": classic_best.to_dict(),
        "classic_tuned_tune": classic_tune, "classic_tuned_test": classic_test,
        "tuned_params": best.to_dict(),
        "tuned_tune": tuned_tune, "tuned_test": tuned_test,
        "ranking_model_params": ranking_model.to_dict(),
        "ranking_model_tune": ranking_tune, "ranking_model_test": ranking_test,
        "market_comparison_2014_2023": mkt,
        "grid_top5": grid.head(5).to_dict(orient="records"),
    }
    (OUT / "backtest_report.json").write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
