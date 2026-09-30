# REAL Fighter Rankings: Methodology

*Results, Evidence, Analytics, Ledger.* Data through 2026-09-26. This document is generated from the live configuration (`config/weights.yaml`) and the audit trail (`outputs/audit_top30.csv`) on every rebuild.

## 1. What the rank means

A resume rank: who has earned the position as of today, updated weekly after each event. It is not a prediction of who would win a fight tomorrow; that is a separate model (section 8), tracked on its own. Champions and interim champions sit above the numbered board. Contenders are numbered 1 to 30.

## 2. Data and how far to trust it

| Source | What it provides | Coverage | Reliability |
|---|---|---|---|
| UFCStats (official UFC statistics), via the Greco1899 open scraper | Every UFC bout: result, method, round, time, judges' scorecards, round-by-round strikes, knockdowns, takedowns, submission attempts, control time | 8,911 bouts, 1994 to 2026-09-26; round stats for 99.8%; all three judges' cards for 98.6% of decisions (100% since 2005) | High for what it records. Strike counts are hand-coded and do not measure damage. Judges' cards are official but can be wrong. |
| Hand-kept configuration files | Retirements and releases, documented injury layoffs, announced division moves, vacant titles, interim champions | As maintained, each entry carries its reason and source | Only as current as the last edit; every entry is listed in `config/` |
| Public boards (UFC media panel, Meta UFC Rankings, Sherdog, Fight Matrix, ESPN) | Comparison only; never an input to the score | Snapshots stored in `data/external/` with their dates | Used to find disagreements, not to copy |

Known gaps: no pre-UFC records (debutants start at the same rating), no injury data beyond the hand-kept list, no contract or matchmaking information, and statistics before about 2001 are sparse.

## 3. How A + B = C: the pipeline, in order

1. **Resume rating.** Every UFC bout since 1994 is processed in date order. Each fighter's rating moves by K x (actual score - expected score), where the expected score comes from the two ratings (Elo). Rules for scoring a result are in section 4.
2. **Eligibility.** A fighter must have fought within the active window, be on the roster, and be in a ranked division (section 6).
3. **Quality ledger.** Wins and losses are re-read for resume value (section 5).
4. **Score.** Score = rating weight x scaled rating + ledger weight x scaled ledger - form penalty. Both inputs are scaled within the division by their interdecile range: (value - median) / (90th percentile - 10th percentile).
5. **Head-to-head.** The winner of the latest meeting moves above the loser when close enough (section 7).
6. **Title cycle.** Recent title-fight challengers who lost step back from the top slots (section 7).
7. **Stability band.** The same board is rebuilt with nearby weights; the band is each fighter's 10th to 90th percentile position.
8. **Audit.** Every contender's placement records where the score put him and which rule moved him.

## 4. Scoring a single fight (the rating)

| Situation | Winner's score (loser gets 1 minus this) | Why |
|---|---|---|
| Knockout, TKO or submission | 1.0 | A finish is a complete result |
| Decision | 50% judges' cards + 50% fight statistics, never below 0.5 for the official winner | Judges alone can be wrong (Jones vs. Reyes); stats alone ignore what judges see. The official result always stands. |
| Judges' card, per judge | 1-point margin (29-28, 48-47) = 0.6; 2 points = 0.8; 3+ points (30-27, 49-46, 50-45) = 1.0 | 29-28 and 48-47 are close; 49-46 is a clear win |
| Fight statistics | Logistic of the winner's dominance per minute: significant strike difference + 5 x knockdowns + 2 x takedowns + 2 x submission attempts + control-time difference in minutes | Same formula as the validated predictive model |

K = 60, and 1.5 x K for a fighter's first 5 UFC bouts. There is no rating decay for time off; inactivity is handled in section 6.

**Loss rules.** A loss is **dominant** when it is a first-round finish, an early finish (first half of the scheduled rounds) while clearly behind on the stats, or a decision with 2 of 3 cards at 3+ points where the stats do not contradict the cards. A late finish while close on the stats (winner ahead by 1.5 or less per minute), a split or majority decision, or a decision scored 0.7 or less is **close**.

| Loss | Rating cost | Why |
|---|---|---|
| Close loss to a top-5 fighter by someone outside the top 5 | A gain of 10% of K | Proof of concept: you showed you belong at that level |
| Loss to a top-3 fighter or in a title fight, not dominant | 15% of the normal drop (60% if the previous bout was also a loss) | Losing to the best is expected; a losing streak is not a one-off |
| Same, but dominant | 75% | A blowout says the gap is real, even at the top (Della Maddalena vs. Makhachev) |
| First-round finish by a heavy favorite (75%+ pre-fight win probability) | 100% | The real gap, confirmed; no need to run it back |
| Any other loss | 100% | |
| First-round finish by the underdog | Both fighters move 70% as much | Quick early finishes can be flukes |

## 5. The quality ledger

A **quality win** is a win over a UFC fighter who had 5+ UFC wins or was ranked in the division top 7 at the time. Every ledger item is weighted by its age:

| Age of the result | up to 3 years | up to 5 years | up to 10 years | up to 15 years |
|---|---|---|---|---|
| Weight | 1.0 | 0.6 | 0.3 | 0.1 |

| Ledger item | Value | Window |
|---|---|---|
| Quality win | +1.0 | 15 years, age-weighted |
| Proof-of-concept loss (close loss to a top-5 fighter) | +0.5 | 15 years, age-weighted |
| Dominant loss | -1.0 | last 3 years |
| Any other loss to someone outside the top 5 | -1.0 | last 3 years |

**Entrenched** (shown as E) = 5 or more quality wins in 15 years. Activity alone earns nothing: a fighter who takes many fights and loses to non-elite opponents gives the ledger back.

## 6. Eligibility, form and division

- **Inactivity.** No penalty for the first 365 days; up to 50 rating points by 540 days; off the board after that. Documented injury layoffs (`config/layoffs.yaml`) carry no penalty and stay eligible up to 730 days.
- **Form (last five UFC bouts).** Subtracted from the score: 2-3: 0.15, 1-4: 0.45, 0-5: 0.6. A 2-3 is a warning; 1-4 counts seriously against a fighter. A fighter with a negative last five also gets no head-to-head lift.
- **Division.** Two straight bouts in a division settle it. Otherwise the division fought in most over the last 3 years, with ties going to the division of the most recent win. Title holders are ranked in their title's division. Announced moves are in `config/division_overrides.yaml`, each with its reason.
- **Roster.** Retirements and releases are removed (`config/roster_exclusions.yaml`).

## 7. Matchmaking reality rules

- **Head-to-head.** If a fighter beat someone in their most recent meeting within 3 years and sits no more than 3 places below him (6 if the fight was in the last 12 months), he moves directly above him.
- **Title cycle.** A challenger who lost a title fight in the last 365 days and has not won since is placed no higher than #4: still close, but the champion is fighting someone else next. A champion who lost the belt is exempt (immediate rematches are common). Anyone that challenger beat in the last year stays below him.

## 8. Validation

Agreement with the public boards (UFC contenders only, champions removed): our average gap is 1.9 to 2.2 places; the public boards differ from each other by 0.9 to 1.6. Disagreement is expected and reported, not removed: `outputs/compare_flags.csv` lists every large gap with its cause.

The separate predictive model (performance-adjusted Elo) scores 61.2% accuracy and 0.6621 log loss on 3,390 held-out bouts from 2020 on, against 58.1% for results-only Elo and 65.2% for the betting market (2014-2023).

## 9. Worked examples (from this rebuild's audit trail)

| Division | Fighter | Final | How he got there | Rating term | Ledger term | Form | Ledger detail | Last 5 |
|---|---|---|---|---|---|---|---|---|
| Bantamweight | Mario Bautista | #5 | score order #5 | +0.50 | +0.22 | -0.00 | +3.6 QW +0.0 proof -1.0 blowout -0.0 weak | 4-1 |
| Bantamweight | Cory Sandhagen | #9 | score order #7; head-to-head -> #9 | +0.67 | +0.14 | -0.15 | +4.3 QW +0.0 proof -2.0 blowout -1.0 weak | 2-3 |
| Light Heavyweight | Jiri Prochazka | #4 | score order #2; title cycle -> #4 | +0.57 | +0.19 | -0.00 | +4.2 QW +0.5 proof -2.0 blowout -0.0 weak | 3-2 |
| Light Heavyweight | Khalil Rountree Jr. | #8 | score order #8 | +0.26 | +0.21 | -0.00 | +2.6 QW +0.5 proof -0.0 blowout -0.0 weak | 3-2 |
| Heavyweight | Alex Pereira | #4 | score order #1; title cycle -> #4 | +0.76 | +0.51 | -0.00 | +7.4 QW +0.0 proof -1.0 blowout -0.0 weak | 3-2 |
| Welterweight | Kamaru Usman | #9 | score order #9 | +0.75 | +0.15 | -0.45 | +4.3 QW +0.0 proof -1.0 blowout -1.0 weak | 1-4 |
| Welterweight | Kevin Holland | #11 | score order #10; head-to-head -> #11 | +0.30 | +0.13 | -0.00 | +7.0 QW +0.0 proof -2.0 blowout -3.0 weak | 3-2 |
| Flyweight | Brandon Moreno | #6 | score order #5; title cycle -> #6 | +0.39 | +0.14 | -0.00 | +3.7 QW +0.0 proof -0.0 blowout -2.0 weak | 3-2 |
| Lightweight | Max Holloway | #3 | score order #1; head-to-head -> #3 | +0.92 | +0.43 | -0.00 | +7.1 QW +0.0 proof -1.0 blowout -0.0 weak | 3-2 |

## 10. Limits and open decisions

- Pre-UFC records are not yet used; they will set starting ratings and judge debut opponents' quality, never award ranking credit directly.
- Division overrides, injuries and retirements are hand-kept and need weekly review.
- Weights and thresholds were set by stated judgment and checked against the public boards; they have not been fitted to any outcome.
- Card-quality and matchmaking analyses use the predictive model's positions, not these boards.

Independent fan and research project. Not affiliated with, sponsored or endorsed by UFC, Zuffa, LLC, TKO Group Holdings, or any athlete.