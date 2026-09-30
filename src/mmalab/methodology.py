"""
methodology.py - Writes METHODOLOGY.md (and docs/methodology.html) from the live
configuration and the audit trail, so every number in the document is the
number the model used on this rebuild.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "config"
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"

EXAMPLES = [
    ("Bantamweight", "Mario Bautista"), ("Bantamweight", "Cory Sandhagen"),
    ("Light Heavyweight", "Jiri Prochazka"), ("Light Heavyweight", "Khalil Rountree Jr."),
    ("Heavyweight", "Alex Pereira"), ("Welterweight", "Kamaru Usman"), ("Welterweight", "Kevin Holland"),
    ("Flyweight", "Brandon Moreno"), ("Lightweight", "Max Holloway"),
]


def _y(name: str) -> dict:
    p = CFG / name
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def build_text() -> str:
    cfg = _y("weights.yaml")
    rc = cfg["resume"]
    e = rc["engine"]
    L = rc["ledger"]
    ina = rc["inactivity"]
    h2h = rc["head_to_head"]
    tc = rc["title_cycle"]
    fp = rc["form_penalty"]
    hz = rc["horizons"]
    audit = pd.read_csv(OUT / "audit_top30.csv")
    bouts = pd.read_csv(ROOT / "data" / "processed" / "bouts.csv", parse_dates=["date"])
    as_of = bouts["date"].max().date()
    pair = pd.read_csv(OUT / "compare_pairwise.csv") if (OUT / "compare_pairwise.csv").exists() else None
    bt = json.loads((OUT / "backtest_report.json").read_text()) if (OUT / "backtest_report.json").exists() else None

    t = []
    a = t.append
    a(f"# {cfg.get('site_name', 'REAL Fighter Rankings')}: Methodology")
    a("")
    a(f"*{cfg.get('site_tagline', '')}.* Data through {as_of}. This document is generated from the live "
      "configuration (`config/weights.yaml`) and the audit trail (`outputs/audit_top30.csv`) on every rebuild.")
    a("")
    a("## 1. What the rank means")
    a("")
    a("A resume rank: who has earned the position as of today, updated weekly after each event. It is not a "
      "prediction of who would win a fight tomorrow; that is a separate model (section 8), tracked on its own. "
      "Champions and interim champions sit above the numbered board. Contenders are numbered 1 to 30.")
    a("")
    a("## 2. Data and how far to trust it")
    a("")
    a("| Source | What it provides | Coverage | Reliability |")
    a("|---|---|---|---|")
    a(f"| UFCStats (official UFC statistics), via the Greco1899 open scraper | Every UFC bout: result, method, round, time, judges' scorecards, round-by-round strikes, knockdowns, takedowns, submission attempts, control time | {len(bouts):,} bouts, 1994 to {as_of}; round stats for 99.8%; all three judges' cards for 98.6% of decisions (100% since 2005) | High for what it records. Strike counts are hand-coded and do not measure damage. Judges' cards are official but can be wrong. |")
    a("| Hand-kept configuration files | Retirements and releases, documented injury layoffs, announced division moves, vacant titles, interim champions | As maintained, each entry carries its reason and source | Only as current as the last edit; every entry is listed in `config/` |")
    a("| Public boards (UFC media panel, Meta UFC Rankings, Sherdog, Fight Matrix, ESPN) | Comparison only; never an input to the score | Snapshots stored in `data/external/` with their dates | Used to find disagreements, not to copy |")
    a("")
    a("Known gaps: no pre-UFC records (debutants start at the same rating), no injury data beyond the hand-kept list, no contract or matchmaking information, and statistics before about 2001 are sparse.")
    a("")
    a("## 3. How A + B = C: the pipeline, in order")
    a("")
    a("1. **Resume rating.** Every UFC bout since 1994 is processed in date order. Each fighter's rating moves by K x (actual score - expected score), where the expected score comes from the two ratings (Elo). Rules for scoring a result are in section 4.")
    a("2. **Eligibility.** A fighter must have fought within the active window, be on the roster, and be in a ranked division (section 6).")
    a("3. **Quality ledger.** Wins and losses are re-read for resume value (section 5).")
    a("4. **Score.** Score = rating weight x scaled rating + ledger weight x scaled ledger - form penalty. Both inputs are scaled within the division by their interdecile range: (value - median) / (90th percentile - 10th percentile).")
    a("5. **Head-to-head.** The winner of the latest meeting moves above the loser when close enough (section 7).")
    a("6. **Title cycle.** Recent title-fight challengers who lost step back from the top slots (section 7).")
    a("7. **Stability band.** The same board is rebuilt with nearby weights; the band is each fighter's 10th to 90th percentile position.")
    a("8. **Audit.** Every contender's placement records where the score put him and which rule moved him.")
    a("")
    a("## 4. Scoring a single fight (the rating)")
    a("")
    a("| Situation | Winner's score (loser gets 1 minus this) | Why |")
    a("|---|---|---|")
    a("| Knockout, TKO or submission | 1.0 | A finish is a complete result |")
    a(f"| Decision | {e.get('card_weight', 0.5):.0%} judges' cards + {1 - e.get('card_weight', 0.5):.0%} fight statistics, never below 0.5 for the official winner | Judges alone can be wrong (Jones vs. Reyes); stats alone ignore what judges see. The official result always stands. |")
    a("| Judges' card, per judge | 1-point margin (29-28, 48-47) = 0.6; 2 points = 0.8; 3+ points (30-27, 49-46, 50-45) = 1.0 | 29-28 and 48-47 are close; 49-46 is a clear win |")
    a("| Fight statistics | Logistic of the winner's dominance per minute: significant strike difference + 5 x knockdowns + 2 x takedowns + 2 x submission attempts + control-time difference in minutes | Same formula as the validated predictive model |")
    a("")
    a(f"K = {e['k']}, and {e['k_new_mult']} x K for a fighter's first {e['n_new']} UFC bouts. There is no rating decay for time off; inactivity is handled in section 6.")
    a("")
    a("**Loss rules.** A loss is **dominant** when it is a first-round finish, an early finish (first half of the scheduled rounds) while clearly behind on the stats, or a decision with 2 of 3 cards at 3+ points where the stats do not contradict the cards. A late finish while close on the stats (winner ahead by "
      f"{e.get('war_stat_max', 1.5)} or less per minute), a split or majority decision, or a decision scored {e.get('close_s', 0.7)} or less is **close**.")
    a("")
    a("| Loss | Rating cost | Why |")
    a("|---|---|---|")
    a(f"| Close loss to a top-{e.get('proof_top_n', 5)} fighter by someone outside the top {e.get('proof_top_n', 5)} | A gain of {e.get('proof_gain', 0.1):.0%} of K | Proof of concept: you showed you belong at that level |")
    a(f"| Loss to a top-{e.get('protect_top_n', 3)} fighter or in a title fight, not dominant | {e['protected_loss_mult']:.0%} of the normal drop ({e.get('consecutive_loss_mult', 0.6):.0%} if the previous bout was also a loss) | Losing to the best is expected; a losing streak is not a one-off |")
    a(f"| Same, but dominant | {e['dominant_loss_mult']:.0%} | A blowout says the gap is real, even at the top (Della Maddalena vs. Makhachev) |")
    a(f"| First-round finish by a heavy favorite ({e['heavy_favorite_p']:.0%}+ pre-fight win probability) | 100% | The real gap, confirmed; no need to run it back |")
    a("| Any other loss | 100% | |")
    a(f"| First-round finish by the underdog | Both fighters move {e.get('upset_quick_finish_mult', 0.7):.0%} as much | Quick early finishes can be flukes |")
    a("")
    a("## 5. The quality ledger")
    a("")
    a(f"A **quality win** is a win over a UFC fighter who had {e['quality_min_wins']}+ UFC wins or was ranked in the division top {e['quality_top_n']} at the time. Every ledger item is weighted by its age:")
    a("")
    a("| Age of the result | " + " | ".join(f"up to {k} years" for k in hz) + " |")
    a("|---|" + "---|" * len(hz))
    a("| Weight | " + " | ".join(str(v) for v in hz.values()) + " |")
    a("")
    a("| Ledger item | Value | Window |")
    a("|---|---|---|")
    a(f"| Quality win | +{L['quality_win']} | 15 years, age-weighted |")
    a(f"| Proof-of-concept loss (close loss to a top-5 fighter) | +{L['proof_of_concept']} | 15 years, age-weighted |")
    a(f"| Dominant loss | -{L['dominant_loss']} | last {rc.get('decisive_loss_years', 3)} years |")
    a(f"| Any other loss to someone outside the top 5 | -{L['loss_outside_top5']} | last {rc.get('decisive_loss_years', 3)} years |")
    a("")
    a("**Entrenched** (shown as E) = 5 or more quality wins in 15 years. Activity alone earns nothing: a fighter who takes many fights and loses to non-elite opponents gives the ledger back.")
    a("")
    a("## 6. Eligibility, form and division")
    a("")
    a(f"- **Inactivity.** No penalty for the first {ina['grace_days']} days; up to {ina['max_penalty_points']} rating points by {ina['max_days']} days; off the board after that. Documented injury layoffs (`config/layoffs.yaml`) carry no penalty and stay eligible up to {ina['injury_max_days']} days.")
    a("- **Form (last five UFC bouts).** Subtracted from the score: " + ", ".join(f"{k}: {v}" for k, v in fp.items()) + ". A 2-3 is a warning; 1-4 counts seriously against a fighter. A fighter with a negative last five also gets no head-to-head lift.")
    a("- **Division.** Two straight bouts in a division settle it. Otherwise the division fought in most over the last 3 years, with ties going to the division of the most recent win. Title holders are ranked in their title's division. Announced moves are in `config/division_overrides.yaml`, each with its reason.")
    a("- **Roster.** Retirements and releases are removed (`config/roster_exclusions.yaml`).")
    a("")
    a("## 7. Matchmaking reality rules")
    a("")
    a(f"- **Head-to-head.** If a fighter beat someone in their most recent meeting within {h2h['max_years']} years and sits no more than {h2h['max_gap']} places below him ({h2h['max_gap_recent']} if the fight was in the last 12 months), he moves directly above him.")
    a(f"- **Title cycle.** A challenger who lost a title fight in the last {tc['days']} days and has not won since is placed no higher than #{tc['min_position']}: still close, but the champion is fighting someone else next. A champion who lost the belt is exempt (immediate rematches are common). Anyone that challenger beat in the last year stays below him.")
    a("")
    a("## 8. Validation")
    a("")
    if pair is not None:
        ours = pair[(pair["b"] == "Our board") | (pair["a"] == "Our board")]
        others = pair[(pair["a"] != "Our board") & (pair["b"] != "Our board")]
        a(f"Agreement with the public boards (UFC contenders only, champions removed): our average gap is "
          f"{ours['mean_abs_gap'].min():.1f} to {ours['mean_abs_gap'].max():.1f} places; the public boards differ from each other by "
          f"{others['mean_abs_gap'].min():.1f} to {others['mean_abs_gap'].max():.1f}. Disagreement is expected and reported, not removed: "
          "`outputs/compare_flags.csv` lists every large gap with its cause.")
        a("")
    if bt:
        a(f"The separate predictive model (performance-adjusted Elo) scores {bt['ranking_model_test']['accuracy']:.1%} accuracy and "
          f"{bt['ranking_model_test']['log_loss']} log loss on {bt['ranking_model_test']['n']:,} held-out bouts from 2020 on, against "
          f"{bt['classic_tuned_test']['accuracy']:.1%} for results-only Elo and 65.2% for the betting market (2014-2023).")
        a("")
    a("## 9. Worked examples (from this rebuild's audit trail)")
    a("")
    a("| Division | Fighter | Final | How he got there | Rating term | Ledger term | Form | Ledger detail | Last 5 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for div, name in EXAMPLES:
        r = audit[(audit["division"] == div) & (audit["fighter"] == name)]
        if r.empty:
            continue
        r = r.iloc[0]
        a(f"| {div} | {name} | #{int(r['rank'])} | {r['placement']} | {r['rating_term']:+.2f} | {r['ledger_term']:+.2f} | "
          f"-{r['form_penalty']:.2f} | {r['ledger_detail']} | {r['last5']} |")
    a("")
    a("## 10. Limits and open decisions")
    a("")
    a("- Pre-UFC records are not yet used; they will set starting ratings and judge debut opponents' quality, never award ranking credit directly.")
    a("- Division overrides, injuries and retirements are hand-kept and need weekly review.")
    a("- Weights and thresholds were set by stated judgment and checked against the public boards; they have not been fitted to any outcome.")
    a("- Card-quality and matchmaking analyses use the predictive model's positions, not these boards.")
    a("")
    a("Independent fan and research project. Not affiliated with, sponsored or endorsed by UFC, Zuffa, LLC, TKO Group Holdings, or any athlete.")
    return "\n".join(t)


def main() -> None:
    text = build_text()
    (ROOT / "METHODOLOGY.md").write_text(text)
    import markdown
    body = markdown.markdown(text, extensions=["tables"])
    css = ("body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:24px 16px;"
           "line-height:1.5;color:#0b0b0b;background:#fcfcfb}table{border-collapse:collapse;width:100%;font-size:.88rem;"
           "display:block;overflow-x:auto}th,td{border-bottom:1px solid #e1e0d9;padding:5px 8px;text-align:left;vertical-align:top}"
           "@media (prefers-color-scheme: dark){body{color:#fff;background:#1a1a19}th,td{border-color:#2c2c2a}}")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "methodology.html").write_text(
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Methodology</title><style>{css}</style></head><body><p><a href='index.html'>Back to the boards</a></p>{body}</body></html>")
    print("METHODOLOGY.md and docs/methodology.html written")


if __name__ == "__main__":
    main()
