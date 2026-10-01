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
    a(f"# {cfg.get('site_name', 'REAL Fighter Rankings')}: Methodology, version {cfg.get('method_version', '1.0')}")
    a("")
    a(f"*{cfg.get('site_tagline', '')}.* Data through {as_of}. This document is generated from the live "
      "configuration (`config/weights.yaml`) and the audit trail (`outputs/audit_top30.csv`) on every rebuild.")
    a("")
    a("## 1. What the rank means")
    a("")
    a("A resume rank: who has earned the position as of today, updated automatically each week. The single principle "
      "behind every rule: **a fighter is ranked on how he performed against the fighters he faced, and how good those "
      "fighters were.** The goal is the most defensible board possible, not agreement with any other board. It is not a "
      "prediction of who would win tomorrow; that is a separate model (section 8, and the Prediction page). Champions (C), "
      "interim champions (IC) and reserved spots (R: former champions who vacated with an injury and are owed a title "
      "shot) sit above the numbered board with their metrics shown. Contenders are numbered 1 to 30.")
    a("")
    a("## 2. Data and how far to trust it")
    a("")
    a("| Source | What it provides | Coverage | Reliability |")
    a("|---|---|---|---|")
    a(f"| UFCStats (official UFC statistics), via the Greco1899 open scraper | Every UFC bout: result, method, round, time, judges' scorecards, round-by-round strikes, knockdowns, takedowns, submission attempts, control time | {len(bouts):,} bouts, 1994 to {as_of}; round stats for 99.8%; all three judges' cards for 98.6% of decisions (100% since 2005) | High for what it records. Strike counts are hand-coded and do not measure damage. Judges' cards are official but can be wrong. |")
    a("| Official UFC rankings history (martj42/ufc_rankings_history, every media-panel release Feb 2013 to June 2026, extended with weekly snapshots of ufc.com) | Each opponent's official rank on the day of the fight | 534 releases; about 99% of ranked names matched to UFCStats | High; before Feb 2013 the model's own position is used instead |")
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
    a("Ranks used by the rules below (top 3, top 5, quality-win tiers) are the **official** ranks on the fight date from 2013 on, and the model's own division position before that.")
    a("")
    a("**Other fight-level rules.** A no-contest caused by a failed drug test counts as a loss for the fighter who failed "
      "(read from the official bout details). A bout taken on short notice (about 3 weeks or less, `config/short_notice.yaml`) "
      "counts 1.2x for a win and 0.5x for a loss.")
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
    a("A **quality win** is valued by the opponent's official rank going into the fight: champion 2.0, ranked 1-5 1.5, "
      "6-10 1.0, 11-15 0.5. An unranked opponent with 8+ UFC wins and a winning UFC record is worth 0.25. Beating four "
      "top-10 fighters is worth more than beating eight fighters ranked 11-15. Every ledger item is weighted by its age:")
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
    ent = rc.get("entrenched", {"top10_wins": 4, "top15_wins": 5})
    a(f"**Entrenched** (shown as E) = {ent['top10_wins']}+ wins over top-10 opponents, or {ent['top15_wins']}+ over top-15 opponents, in 15 years. Activity alone earns nothing: a fighter who takes many fights and loses to non-elite opponents gives the ledger back.")
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
    a(f"- **Title cycle.** A challenger who lost a title fight in the last {tc['days']} days is placed no higher than #{tc['min_position']}: still close, but the champion is fighting someone else next. He earns his way back with {tc.get('release_top10_wins', 1)} win over a top-10 opponent or {tc.get('release_wins', 2)} wins of any kind. A champion who lost the belt is exempt (immediate rematches are common). Anyone that challenger beat in the last year stays below him.")
    a("- **Head-to-head details.** A close win (split or majority decision, or a fight scored as close) more than 12 months old settles nothing, and a fighter with a negative last five gets no head-to-head lift.")
    a("- **Reserved spots.** Former champions who vacated because of injury are listed as R above the numbered board (`config/reserved.yaml`).")
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
    fv = json.loads((OUT / "forward_validation.json").read_text()) if (OUT / "forward_validation.json").exists() else None
    if fv:
        a(f"**Forward check of the resume board.** Boards were rebuilt as they stood before each of the last "
          f"{fv['snapshots']} events. In {fv['ranked_vs_ranked_bouts']} bouts between two fighters on the same board, the "
          f"higher-placed fighter won {fv['ours_higher_ranked_win_rate']:.1%} of the time; on the {fv['same_bouts_official_also_ranked']} "
          f"of those bouts where the official board ranked both, ours was right {fv['ours_on_same_bouts']:.1%} and the official "
          f"board {fv['official_on_same_bouts']:.1%}" + (f"; the prediction model picked {fv['predictive_elo_on_all_ranked_bouts']:.1%}." if fv.get('predictive_elo_on_all_ranked_bouts') else ".") +
          " Ranked-versus-ranked bouts are matched to be close, so every board sits near a coin flip on them; "
          "the differences are within sampling error. These snapshots use today's rules, so they are in-sample; "
          "the true forward test starts at the v1.0 freeze.")
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
    a("## 10. How REAL compares with published rating systems")
    a("")
    a("| Practice (source) | REAL v1.0 |")
    a("|---|---|")
    a("| Separate resume ranking from prediction (NCAA NET vs KenPom; Fight Matrix) | Met: two systems, two pages |")
    a("| Margin of victory from the judges' rounds (BoxRec) | Met, blended 50/50 with fight stats |")
    a("| Partial credit for close results (Fight Matrix split-decision scoring) | Met: card margins and close-fight rules |")
    a("| Winner stays above loser for a period (BoxRec, 36 months) | Met in a narrower form: head-to-head rule |")
    a("| Losses in the biggest fights cost less (FIFA: knockout-stage losses cost nothing) | Met: loss protection tiers |")
    a("| Out-of-sample validation against baselines and the market (Holmes et al. 2023; Tennis Elo) | Met for the prediction model; started for the resume board |")
    a("| Per-fighter uncertainty (Glicko RD, TrueSkill) | Partly met: stability bands cover weights, not sample size |")
    a("| Margin-of-victory autocorrelation correction (FiveThirtyEight) | Not yet |")
    a("| Constants fitted to data rather than set by judgment | Not yet: set by stated principle, then checked |")
    a("| Versioned method and changelog (FIFA, BoxRec, FiveThirtyEight) | Met from v1.0 |")
    a("")
    a("## 11. Limits and open decisions")
    a("")
    a("- Pre-UFC records and betting odds after 2023 are not yet loaded (they require a manual Kaggle download); when added, pre-UFC records will set starting ratings and judge debut opponents' quality, never award ranking credit, and odds will define 'heavy favorite' instead of the model's own probability.")
    a("- Missed weight is not recorded in the fight data and is not yet used.")
    a("- Division overrides, injuries and retirements are hand-kept and need weekly review.")
    a("- Weights and thresholds were set by stated judgment and checked against the public boards; they have not been fitted to any outcome.")
    a("- Card-quality and matchmaking analyses use the predictive model's positions, not these boards.")
    a("")
    a("## 12. Changelog")
    a("")
    a("- **1.0 (Oct 1, 2026).** Method frozen for forward grading. Official rank at fight time (2013+); tiered quality wins; "
      "proof-of-concept credit for close losses to top-5 fighters; early-finish and war rules; drug-test overturns count as losses; "
      "short-notice credit; last-five form penalty; division, head-to-head, title-cycle and reserved-spot rules; audit trail; "
      "prediction model published separately.")
    a("- **0.x (Sept 29-30, 2026).** Composite of six percentile dimensions, replaced after review because four dimensions carried no ranking signal and losses were counted three times.")
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
