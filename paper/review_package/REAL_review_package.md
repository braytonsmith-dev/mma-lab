# REAL Fighter Rankings: pre-submission review package

Prepared September 30, 2026 for an independent methodology and submission-readiness review. Author: Brayton Smith, PhD, MBA (independent; Marion, Indiana). Everything in this package is generated from the public repository and can be reproduced with `PYTHONPATH=src python3 -m mmalab.run_all`.

## 0. Key facts for the reviewer

- Target venue: MIT Sloan Sports Analytics Conference 2027 (SSAC27), Research Paper Competition, Other Sports track. Conference Feb 25-26, 2027, Boston.
- Abstract deadline: October 1, 2026, 11:59 pm Eastern. Full paper requests late October 2026; full paper due December 4, 2026 if invited.
- Abstract rules (from the SSAC page): under 500 words including title and body; sections Introduction, Methods, Results, Conclusion; up to two combined tables or figures; a link to a public GitHub (or other open) repository with the data is required; code encouraged. Abstracts are judged on novelty, academic rigor and impact.
- Repository: https://github.com/braytonsmith-dev/real-fighter-rankings. Live site: https://braytonsmith-dev.github.io/real-fighter-rankings/ with methodology.html, prediction.html and favorites.html.
- Data: 8,911 UFC bouts, 1994-03-11 to 2026-09-26, from UFCStats via an open scraper; official UFC media-panel rankings history (every release Feb 2013 to June 2026) for opponent rank at fight time; closing odds Nov 2014 to Dec 2023 for the market comparison.
- Two separate models: (1) a predictive performance-adjusted Elo, validated out of sample, used for the abstract's prediction claims and the card-quality index; (2) the REAL resume board (v1.0, frozen Oct 1, 2026), which is the public ranking product and is described in the abstract's conclusion.

## 1. The abstract as it will be submitted (497 words including title)

# Performance-Adjusted Elo for Mixed Martial Arts: In-Fight Statistics Improve UFC Rankings and Measure the Card-Quality Gap

Track: Other Sports. Author: Brayton Smith, PhD, MBA. Repository: https://github.com/braytonsmith-dev/real-fighter-rankings

## Introduction

In June 2026 the UFC began replacing its media-voted rankings with an Elo-style model built with Meta that uses results, opponent quality, and recency. Two questions decide whether a data-driven ranking deserves trust: does it predict outcomes, and what does it reveal about matchmaking? We build an open, reproducible rating system from public UFCStats data, test whether round-level statistics improve on results-only Elo, and measure how ranked-versus-ranked bouts are distributed across the promotion's 43-event calendar.

## Methods

Data: 8,911 UFC bouts from March 1994 to September 2026 with round-level statistics for 99.8%. Classic Elo updates on the binary result. Performance-adjusted Elo replaces the result with a blend of the result and a logistic transform of a per-minute dominance differential (significant strikes, knockdowns weighted 5, takedowns 2, submission attempts 2, control time), with a floor so a win never scores below 0.5. Both variants use a larger K for a fighter's first five UFC bouts and regression toward the mean after layoffs longer than a year. All parameters were chosen by grid search on 2010-2019 bouts (log loss) and evaluated once on 3,390 held-out 2020-2026 bouts. Ratings were also compared with de-vigged closing odds on 3,499 matched bouts (2014-2023). For every event since 2022, each fighter was positioned within their division among fighters active in the prior 18 months by pre-fight rating, and a bout was tagged "top 10" when both fighters sat inside positions 1-11 (champion plus ten).

## Results

Table 1 summarizes prediction. Performance adjustment lowers held-out log loss from 0.674 to 0.662 and raises accuracy from 58.1% to 61.2%; a 90% weight on dominance is optimal, and finish multipliers add nothing once dominance is included. The betting market remains stronger (0.616, 65.2%), so the model is a ranking instrument rather than a betting edge. Figure 1 shows the card-quality index: 203 cards from 2022 through September 2026 average 1.2 top-10 bouts each, numbered events 2.2 and Fight Nights 0.7, and 31% to 54% of Fight Nights carry none. Supply binds before scheduling does: fighters who begin a year inside a top 11 average 1.3 to 1.4 bouts that year, 12% to 16% do not compete at all (2022-2025), and 58% to 62% of their bouts are already against another top-11 opponent, which caps the achievable number of ranked bouts near 50 per year.

## Conclusion

Round-level statistics carry ranking information that results alone miss. We pair the predictive model with REAL Fighter Rankings, a weekly resume board that values each win by the opponent's official rank at fight time, blends judges' cards with fight statistics, and publishes an audit trail for every placement. The card-quality index confirms the "stacked card" complaint but bounds the remedy: with roughly 50 ranked-versus-ranked bouts available per year, redistribution across 43 cards, not more matchups, is the actionable lever. Code, data, and weekly boards are open source at the repository above.

Table 1 to be attached (from outputs/table_backtest.md):

| Model | Log loss, tune 2010-19 | Log loss, test 2020-26 | Brier, test | Accuracy, test |
|---|---|---|---|---|
| Coin flip | - | 0.6931 | - | 50.0% |
| Classic Elo, untuned (K=32) | 0.6849 | 0.6838 | 0.2454 | 56.5% |
| Classic Elo, tuned (results only) | 0.6801 | 0.674 | 0.2406 | 58.1% |
| Performance-adjusted Elo, tuned | 0.6639 | 0.6631 | 0.2352 | 60.6% |
| Performance-adjusted Elo, interpretable (win/finish floors) | 0.6675 | 0.6621 | 0.2347 | 61.2% |

Test bouts: 3,390. Tuning bouts: 4,116.

Same-bout comparison against the closing betting market (de-vigged), 3,499 bouts, 2014-11-07 to 2023-12-16:

| Model | Log loss | Brier | Accuracy |
|---|---|---|---|
| Performance-adjusted Elo | 0.6683 | 0.2376 | 59.6% |
| Betting market | 0.6159 | 0.2139 | 65.2% |
| 50/50 blend | 0.6319 | 0.2205 | 64.9% |

Figure 1 to be attached: fig_card_quality.png (top-10 vs top-10 bouts per card and share of cards with none, numbered vs Fight Night, 2022-2026). Figure 2 (optional, if the two-visual limit allows a table plus one figure only, this one is dropped): fig_backtest.png (log loss by year with the held-out window shaded, and a calibration plot).

## 2. Prediction model: full backtest report

Protocol: warm-up 1994-2009 (ratings accumulate, never scored); tuning 2010-2019 (grid search on log loss); test 2020-2026 (scored once with the tuned parameters). Market comparison on the same bouts, de-vigged closing odds.

```json
{
 "protocol": {
  "warmup": "1994-2009",
  "tune": "2010-2019",
  "test": "2020-2026 (through last scraped event)"
 },
 "baseline_params": {
  "k": 32,
  "k_new_mult": 1.0,
  "n_new": 5,
  "finish_mult": 1.0,
  "split_mult": 1.0,
  "layoff_days": 365,
  "layoff_regress_per_year": 0.0,
  "mov_weight": 0.0,
  "mov_scale": 3.0,
  "win_floor": 0.0,
  "finish_floor": 0.0,
  "start": 1500.0
 },
 "baseline_tune": {
  "n": 4116,
  "log_loss": 0.6849,
  "brier": 0.2459,
  "accuracy": 0.5437
 },
 "baseline_test": {
  "n": 3390,
  "log_loss": 0.6838,
  "brier": 0.2454,
  "accuracy": 0.5649
 },
 "classic_tuned_params": {
  "k": 60.0,
  "k_new_mult": 1.5,
  "n_new": 5,
  "finish_mult": 1.0,
  "split_mult": 0.8,
  "layoff_days": 365,
  "layoff_regress_per_year": 0.25,
  "mov_weight": 0.0,
  "mov_scale": 3.0,
  "win_floor": 0.0,
  "finish_floor": 0.0,
  "start": 1500.0
 },
 "classic_tuned_tune": {
  "n": 4116,
  "log_loss": 0.6801,
  "brier": 0.2436,
  "accuracy": 0.5547
 },
 "classic_tuned_test": {
  "n": 3390,
  "log_loss": 0.674,
  "brier": 0.2406,
  "accuracy": 0.5805
 },
 "tuned_params": {
  "k": 130.0,
  "k_new_mult": 1.5,
  "n_new": 5,
  "finish_mult": 1.0,
  "split_mult": 0.8,
  "layoff_days": 365,
  "layoff_regress_per_year": 0.25,
  "mov_weight": 0.9,
  "mov_scale": 2.0,
  "win_floor": 0.5,
  "finish_floor": 0.0,
  "start": 1500.0
 },
 "tuned_tune": {
  "n": 4116,
  "log_loss": 0.6639,
  "brier": 0.2358,
  "accuracy": 0.5865
 },
 "tuned_test": {
  "n": 3390,
  "log_loss": 0.6631,
  "brier": 0.2352,
  "accuracy": 0.6056
 },
 "ranking_model_params": {
  "k": 100,
  "k_new_mult": 2.0,
  "n_new": 5,
  "finish_mult": 1.0,
  "split_mult": 0.8,
  "layoff_days": 365,
  "layoff_regress_per_year": 0.25,
  "mov_weight": 0.75,
  "mov_scale": 2.0,
  "win_floor": 0.5,
  "finish_floor": 0.75,
  "start": 1500.0
 },
 "ranking_model_tune": {
  "n": 4116,
  "log_loss": 0.6675,
  "brier": 0.2375,
  "accuracy": 0.585
 },
 "ranking_model_test": {
  "n": 3390,
  "log_loss": 0.6621,
  "brier": 0.2347,
  "accuracy": 0.6124
 },
 "market_comparison_2014_2023": {
  "matched_bouts": 3499,
  "date_range": [
   "2014-11-07",
   "2023-12-16"
  ],
  "elo": {
   "n": 3499,
   "log_loss": 0.6683,
   "brier": 0.2376,
   "accuracy": 0.5962
  },
  "market_devigged": {
   "n": 3499,
   "log_loss": 0.6159,
   "brier": 0.2139,
   "accuracy": 0.6519
  },
  "blend_50_50": {
   "n": 3499,
   "log_loss": 0.6319,
   "brier": 0.2205,
   "accuracy": 0.6488
  },
  "coin_flip_log_loss": 0.6931
 }
}
```

Held-out log loss by year (predictive model, 2015 on; 2020-2026 is the test window):

|   date |   n |   log_loss |   brier |   accuracy |
|-------:|----:|-----------:|--------:|-----------:|
|   2015 | 464 |     0.6606 |  0.2339 |     0.6034 |
|   2016 | 483 |     0.6604 |  0.2337 |     0.6087 |
|   2017 | 446 |     0.6624 |  0.235  |     0.5919 |
|   2018 | 469 |     0.6646 |  0.2359 |     0.5991 |
|   2019 | 506 |     0.6817 |  0.2445 |     0.5455 |
|   2020 | 444 |     0.6679 |  0.2369 |     0.6104 |
|   2021 | 497 |     0.672  |  0.2392 |     0.6097 |
|   2022 | 506 |     0.6642 |  0.2358 |     0.6008 |
|   2023 | 504 |     0.6708 |  0.2393 |     0.5833 |
|   2024 | 513 |     0.6583 |  0.2332 |     0.6023 |
|   2025 | 515 |     0.6517 |  0.23   |     0.6252 |
|   2026 | 411 |     0.6568 |  0.232  |     0.6083 |

Calibration on the 2020-2026 test bouts (predicted vs observed win rate by bin):

| bin        |    n |   predicted |   actual |
|:-----------|-----:|------------:|---------:|
| (0.1, 0.2] |    4 |    0.1645   | 0.5      |
| (0.2, 0.3] |   51 |    0.271063 | 0.352941 |
| (0.3, 0.4] |  344 |    0.361346 | 0.430233 |
| (0.4, 0.5] |  961 |    0.460165 | 0.473465 |
| (0.5, 0.6] | 1052 |    0.550965 | 0.603612 |
| (0.6, 0.7] |  731 |    0.641563 | 0.678523 |
| (0.7, 0.8] |  219 |    0.736235 | 0.753425 |
| (0.8, 0.9] |   28 |    0.828696 | 0.714286 |

Dominance differential used by the predictive model, per minute: (significant strikes landed difference) + 5 x (knockdowns difference) + 2 x (takedowns difference) + 2 x (submission attempts difference) + (control seconds difference)/60, divided by fight minutes. The sign of this differential agrees with the official winner in 85.6% of bouts.

## 3. Card-quality index and supply facts

Positions are computed on each event date from pre-fight predictive ratings among fighters active in the prior 540 days in that division; 'top 10' = positions 1-11 (champion plus ten).

|   year | card_type   |   events |   bouts_per_card |   top10_bouts_per_card |   top15_bouts_per_card |   share_cards_zero_top10 |   share_cards_zero_top15 |   ranked_share_of_slots |
|-------:|:------------|---------:|-----------------:|-----------------------:|-----------------------:|-------------------------:|-------------------------:|------------------------:|
|   2022 | Fight Night |       29 |           12     |                  0.69  |                  1.483 |                    0.414 |                    0.103 |                   0.197 |
|   2022 | Numbered    |       13 |           12.538 |                  2.308 |                  3.077 |                    0.077 |                    0.077 |                   0.307 |
|   2023 | Fight Night |       29 |           11.793 |                  0.793 |                  1.345 |                    0.31  |                    0.069 |                   0.189 |
|   2023 | Numbered    |       14 |           12.714 |                  1.857 |                  2.643 |                    0.071 |                    0     |                   0.319 |
|   2024 | Fight Night |       28 |           12.179 |                  0.679 |                  1.25  |                    0.536 |                    0.143 |                   0.182 |
|   2024 | Numbered    |       14 |           12.571 |                  2.214 |                  3.143 |                    0.143 |                    0     |                   0.379 |
|   2025 | Fight Night |       30 |           11.9   |                  0.633 |                  1.4   |                    0.433 |                    0.167 |                   0.185 |
|   2025 | Numbered    |       13 |           12.692 |                  2.462 |                  3.538 |                    0.077 |                    0     |                   0.395 |
|   2026 | Fight Night |       25 |           12.64  |                  0.88  |                  1.4   |                    0.32  |                    0.12  |                   0.215 |
|   2026 | Numbered    |        8 |           12.375 |                  2.125 |                  2.875 |                    0     |                    0     |                   0.336 |

Supply facts: fighters inside a division top 11 on January 1 of each year, their bouts that year, and the share against another top-11 fighter.

```json
{
 "2022": {
  "top11_fighters_on_jan1": 121,
  "mean_bouts_per_fighter": 1.33,
  "annualized_bouts_per_fighter": 1.33,
  "share_with_zero_bouts": 0.14,
  "share_of_their_bouts_vs_top11": 0.602,
  "top10_vs_top10_bouts_total": 50,
  "events": 42,
  "days_covered": 365
 },
 "2023": {
  "top11_fighters_on_jan1": 121,
  "mean_bouts_per_fighter": 1.31,
  "annualized_bouts_per_fighter": 1.31,
  "share_with_zero_bouts": 0.157,
  "share_of_their_bouts_vs_top11": 0.614,
  "top10_vs_top10_bouts_total": 49,
  "events": 43,
  "days_covered": 365
 },
 "2024": {
  "top11_fighters_on_jan1": 121,
  "mean_bouts_per_fighter": 1.38,
  "annualized_bouts_per_fighter": 1.38,
  "share_with_zero_bouts": 0.14,
  "share_of_their_bouts_vs_top11": 0.581,
  "top10_vs_top10_bouts_total": 50,
  "events": 42,
  "days_covered": 366
 },
 "2025": {
  "top11_fighters_on_jan1": 121,
  "mean_bouts_per_fighter": 1.43,
  "annualized_bouts_per_fighter": 1.43,
  "share_with_zero_bouts": 0.124,
  "share_of_their_bouts_vs_top11": 0.578,
  "top10_vs_top10_bouts_total": 51,
  "events": 43,
  "days_covered": 365
 },
 "2026": {
  "top11_fighters_on_jan1": 121,
  "mean_bouts_per_fighter": 1.02,
  "annualized_bouts_per_fighter": 1.39,
  "share_with_zero_bouts": 0.231,
  "share_of_their_bouts_vs_top11": 0.621,
  "top10_vs_top10_bouts_total": 39,
  "events": 33,
  "days_covered": 269
 }
}
```

## 4. REAL resume board: methodology v1.0 (generated from the live configuration)

# REAL Fighter Rankings: Methodology, version 1.0

*Results, Evidence, Analytics, Ledger.* Data through 2026-09-26. This document is generated from the live configuration (`config/weights.yaml`) and the audit trail (`outputs/audit_top30.csv`) on every rebuild.

## 1. What the rank means

A resume rank: who has earned the position as of today, updated automatically each week. The single principle behind every rule: **a fighter is ranked on how he performed against the fighters he faced, and how good those fighters were.** The goal is the most defensible board possible, not agreement with any other board. It is not a prediction of who would win tomorrow; that is a separate model (section 8, and the Prediction page). Champions (C), interim champions (IC) and reserved spots (R: former champions who vacated with an injury and are owed a title shot) sit above the numbered board with their metrics shown. Contenders are numbered 1 to 30.

## 2. Data and how far to trust it

| Source | What it provides | Coverage | Reliability |
|---|---|---|---|
| UFCStats (official UFC statistics), via the Greco1899 open scraper | Every UFC bout: result, method, round, time, judges' scorecards, round-by-round strikes, knockdowns, takedowns, submission attempts, control time | 8,911 bouts, 1994 to 2026-09-26; round stats for 99.8%; all three judges' cards for 98.6% of decisions (100% since 2005) | High for what it records. Strike counts are hand-coded and do not measure damage. Judges' cards are official but can be wrong. |
| Official UFC rankings history (martj42/ufc_rankings_history, every media-panel release Feb 2013 to June 2026, extended with weekly snapshots of ufc.com) | Each opponent's official rank on the day of the fight | 534 releases; about 99% of ranked names matched to UFCStats | High; before Feb 2013 the model's own position is used instead |
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

Ranks used by the rules below (top 3, top 5, quality-win tiers) are the **official** ranks on the fight date from 2013 on, and the model's own division position before that.

**Other fight-level rules.** A no-contest caused by a failed drug test counts as a loss for the fighter who failed (read from the official bout details). A bout taken on short notice (about 3 weeks or less, `config/short_notice.yaml`) counts 1.2x for a win and 0.5x for a loss.

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

A **quality win** is valued by the opponent's official rank going into the fight: champion 2.0, ranked 1-5 1.5, 6-10 1.0, 11-15 0.5. An unranked opponent with 8+ UFC wins and a winning UFC record is worth 0.25. Beating four top-10 fighters is worth more than beating eight fighters ranked 11-15. Every ledger item is weighted by its age:

| Age of the result | up to 3 years | up to 5 years | up to 10 years | up to 15 years |
|---|---|---|---|---|
| Weight | 1.0 | 0.6 | 0.3 | 0.1 |

| Ledger item | Value | Window |
|---|---|---|
| Quality win | +1.0 | 15 years, age-weighted |
| Proof-of-concept loss (close loss to a top-5 fighter) | +0.5 | 15 years, age-weighted |
| Dominant loss | -1.0 | last 3 years |
| Any other loss to someone outside the top 5 | -1.0 | last 3 years |

**Entrenched** (shown as E) = 4+ wins over top-10 opponents, or 5+ over top-15 opponents, in 15 years. Activity alone earns nothing: a fighter who takes many fights and loses to non-elite opponents gives the ledger back.

## 6. Eligibility, form and division

- **Inactivity.** No penalty for the first 365 days; up to 50 rating points by 540 days; off the board after that. Documented injury layoffs (`config/layoffs.yaml`) carry no penalty and stay eligible up to 730 days.
- **Form (last five UFC bouts).** Subtracted from the score: 2-3: 0.15, 1-4: 0.6, 0-5: 0.8. A 2-3 is a warning; 1-4 counts seriously against a fighter. A fighter with a negative last five also gets no head-to-head lift.
- **Division.** Two straight bouts in a division settle it. Otherwise the division fought in most over the last 3 years, with ties going to the division of the most recent win. Title holders are ranked in their title's division. Announced moves are in `config/division_overrides.yaml`, each with its reason.
- **Roster.** Retirements and releases are removed (`config/roster_exclusions.yaml`).

## 7. Matchmaking reality rules

- **Head-to-head.** If a fighter beat someone in their most recent meeting within 3 years and sits no more than 3 places below him (6 if the fight was in the last 12 months), he moves directly above him.
- **Title cycle.** A challenger who lost a title fight in the last 270 days is placed no higher than #4: still close, but the champion is fighting someone else next. He earns his way back with 1 win over a top-10 opponent or 2 wins of any kind. A champion who lost the belt is exempt (immediate rematches are common). Anyone that challenger beat in the last year stays below him.
- **Head-to-head details.** A close win (split or majority decision, or a fight scored as close) more than 12 months old settles nothing, and a fighter with a negative last five gets no head-to-head lift.
- **Reserved spots.** Former champions who vacated because of injury are listed as R above the numbered board (`config/reserved.yaml`).

## 8. Validation

Agreement with the public boards (UFC contenders only, champions removed): our average gap is 1.6 to 1.9 places; the public boards differ from each other by 0.9 to 1.6. Disagreement is expected and reported, not removed: `outputs/compare_flags.csv` lists every large gap with its cause.

The separate predictive model (performance-adjusted Elo) scores 61.2% accuracy and 0.6621 log loss on 3,390 held-out bouts from 2020 on, against 58.1% for results-only Elo and 65.2% for the betting market (2014-2023).

**Forward check of the resume board.** Boards were rebuilt as they stood before each of the last 127 events. In 226 bouts between two fighters on the same board, the higher-placed fighter won 54.4% of the time; on the 204 of those bouts where the official board ranked both, ours was right 55.4% and the official board 52.0%; the prediction model picked 62.4%. Ranked-versus-ranked bouts are matched to be close, so every board sits near a coin flip on them; the differences are within sampling error. These snapshots use today's rules, so they are in-sample; the true forward test starts at the v1.0 freeze.

## 9. Worked examples (from this rebuild's audit trail)

| Division | Fighter | Final | How he got there | Rating term | Ledger term | Form | Ledger detail | Last 5 |
|---|---|---|---|---|---|---|---|---|
| Bantamweight | Mario Bautista | #5 | score order #5 | +0.48 | +0.23 | -0.00 | +3.6 QW +0.0 proof -1.0 blowout -0.0 weak | 4-1 |
| Bantamweight | Cory Sandhagen | #6 | score order #6 | +0.64 | +0.21 | -0.15 | +5.3 QW +0.0 proof -2.0 blowout -1.0 weak | 2-3 |
| Light Heavyweight | Jiri Prochazka | #4 | score order #2; title cycle -> #4 | +0.54 | +0.29 | -0.00 | +6.5 QW +0.0 proof -2.0 blowout -0.0 weak | 3-2 |
| Light Heavyweight | Khalil Rountree Jr. | #9 | score order #9 | +0.22 | +0.22 | -0.00 | +3.1 QW +0.0 proof -0.0 blowout -0.0 weak | 3-2 |
| Heavyweight | Alex Pereira | #4 | score order #1; title cycle -> #4 | +0.73 | +0.46 | -0.00 | +10.5 QW +0.0 proof -1.0 blowout -0.0 weak | 3-2 |
| Welterweight | Kamaru Usman | #10 | score order #10 | +0.75 | +0.27 | -0.60 | +5.2 QW +0.0 proof -1.0 blowout -0.0 weak | 1-4 |
| Welterweight | Kevin Holland | #24 | score order #24 | +0.31 | -0.11 | -0.00 | +1.8 QW +0.0 proof -2.0 blowout -3.0 weak | 3-2 |
| Flyweight | Brandon Moreno | #6 | score order #4; title cycle -> #6 | +0.36 | +0.29 | -0.00 | +6.8 QW +0.0 proof -0.0 blowout -1.0 weak | 3-2 |
| Lightweight | Max Holloway | #2 | score order #1; head-to-head -> #2 | +0.93 | +0.63 | -0.00 | +8.4 QW +0.0 proof -1.0 blowout -0.0 weak | 3-2 |

## 10. How REAL compares with published rating systems

| Practice (source) | REAL v1.0 |
|---|---|
| Separate resume ranking from prediction (NCAA NET vs KenPom; Fight Matrix) | Met: two systems, two pages |
| Margin of victory from the judges' rounds (BoxRec) | Met, blended 50/50 with fight stats |
| Partial credit for close results (Fight Matrix split-decision scoring) | Met: card margins and close-fight rules |
| Winner stays above loser for a period (BoxRec, 36 months) | Met in a narrower form: head-to-head rule |
| Losses in the biggest fights cost less (FIFA: knockout-stage losses cost nothing) | Met: loss protection tiers |
| Out-of-sample validation against baselines and the market (Holmes et al. 2023; Tennis Elo) | Met for the prediction model; started for the resume board |
| Per-fighter uncertainty (Glicko RD, TrueSkill) | Partly met: stability bands cover weights, not sample size |
| Margin-of-victory autocorrelation correction (FiveThirtyEight) | Not yet |
| Constants fitted to data rather than set by judgment | Not yet: set by stated principle, then checked |
| Versioned method and changelog (FIFA, BoxRec, FiveThirtyEight) | Met from v1.0 |

## 11. Limits and open decisions

- Pre-UFC records and betting odds after 2023 are not yet loaded (they require a manual Kaggle download); when added, pre-UFC records will set starting ratings and judge debut opponents' quality, never award ranking credit, and odds will define 'heavy favorite' instead of the model's own probability.
- Missed weight is not recorded in the fight data and is not yet used.
- Division overrides, injuries and retirements are hand-kept and need weekly review.
- Weights and thresholds were set by stated judgment and checked against the public boards; they have not been fitted to any outcome.
- Card-quality and matchmaking analyses use the predictive model's positions, not these boards.

## 12. Changelog

- **1.0 (Oct 1, 2026).** Method frozen for forward grading. Official rank at fight time (2013+); tiered quality wins; proof-of-concept credit for close losses to top-5 fighters; early-finish and war rules; drug-test overturns count as losses; short-notice credit; last-five form penalty; division, head-to-head, title-cycle and reserved-spot rules; audit trail; prediction model published separately.
- **0.x (Sept 29-30, 2026).** Composite of six percentile dimensions, replaced after review because four dimensions carried no ranking signal and losses were counted three times.

Independent fan and research project. Not affiliated with, sponsored or endorsed by UFC, Zuffa, LLC, TKO Group Holdings, or any athlete.

## 5. Configuration file (every tunable number)

```yaml
site_name: "REAL Fighter Rankings"
site_tagline: "Results, Evidence, Analytics, Ledger"
method_version: "1.0"

# Composite ranking weights. Must sum to 1.0. Change these and re-run
#   python -m mmalab.rankings
# Each dimension is percentile-ranked within the division before weighting,
# so a weight is "how much of the final score this dimension controls".

weights:
  rating: 0.45        # current performance-adjusted Elo (opponent quality + dominance)
  form_3y: 0.10       # net Elo gained over the last 36 months, after the first two UFC bouts
  entrenchment: 0.20  # UFC tenure and wins over division top-15 opponents
  offense: 0.10       # strike output, differential, knockdowns, takedowns, sub attempts
  activity: 0.05      # bouts in last 24 months, penalty for days since last bout
  durability: 0.10    # strikes absorbed per minute (inverse) and finish-loss rate (inverse)

# Eligibility
division_rule: latest       # latest = division of most recent bout; mode3 = most common of last three
active_window_days: 540      # last bout within ~18 months to appear on a board
min_ufc_bouts: 1
board_size: 30

# Elo parameters for the rating dimension. This is the "interpretable" model:
# 75% of each update listens to in-fight dominance, a win never scores below
# 0.5, a finish never below 0.75. outputs/backtest_report.json reports how
# little predictive accuracy this costs versus the unconstrained optimum.
elo:
  k: 100
  k_new_mult: 2.0
  n_new: 5
  finish_mult: 1.0
  split_mult: 0.8
  layoff_days: 365
  layoff_regress_per_year: 0.25
  mov_weight: 0.75
  mov_scale: 2.0
  win_floor: 0.5
  finish_floor: 0.75

# Rank stability: number of random weight vectors drawn around the weights above
stability_draws: 300
stability_concentration: 40   # higher = draws stay closer to the configured weights

# ---------------------------------------------------------------------------
# Resume board (Option B, adopted Sept 30, 2026). run_all uses this when
# board_model is "resume"; the older composite above stays available as "composite".
board_model: resume
resume:
  weights: {rating: 0.70, quality_wins: 0.30}
  horizons: {3: 1.0, 5: 0.6, 10: 0.3, 15: 0.1}     # age of a quality win in years -> weight
  engine:
    k: 60
    k_new_mult: 1.5
    n_new: 5
    protected_loss_mult: 0.15      # loss to a top-3 fighter or in a title fight, not dominant
    dominant_loss_mult: 0.75       # same, but dominant (2 of 3 cards at 3+ points, stats agree, or R1 finish)
    heavy_favorite_p: 0.75         # R1 finish by a >= 75% favorite: full cost
    consecutive_loss_mult: 0.60    # protection is weaker on a second straight loss
    card_weight: 0.5               # decisions: half judges' cards, half fight stats
    protect_top_n: 3
    quality_top_n: 7
    quality_min_wins: 5
  inactivity:
    grace_days: 365                # no penalty for the first 12 months
    max_days: 540                  # gradual penalty to 18 months, then off the board
    max_penalty_points: 50
    injury_max_days: 730           # documented injuries (config/layoffs.yaml): no penalty, eligible 24 months
  decisive_loss_years: 3         # losses this recent count against the ledger
  ledger:                        # quality ledger, each item weighted by the age horizons above
    quality_win: 1.0             # multiplier on tiered wins: champion 2.0, top 5 1.5, top 10 1.0, top 15 0.5, proven unranked vet 0.25
    proof_of_concept: 0.5        # close loss to a top-5 fighter by someone outside the top 5
    dominant_loss: 1.0           # blowout loss (last 3 years)
    loss_outside_top5: 1.0       # any other loss to someone outside the top 5 (last 3 years)
  form_penalty: {"2-3": 0.15, "1-4": 0.60, "0-5": 0.80}   # score units subtracted for the last five
  title_cycle: {days: 270, min_position: 4, release_top10_wins: 1, release_wins: 2}   # losing challengers; released by 1 top-10 win or 2 wins
  entrenched: {top10_wins: 4, top15_wins: 5}              # in the last 15 years
  head_to_head: {max_gap: 3, max_gap_recent: 6, max_years: 3}   # recent = last 12 months
  declining_guard: false         # proposal: negative last five -> only last-3-year quality wins count
  stability_draws: 200
  stability_concentration: 20

```

## 6. Validation of the resume board

Forward check (in-sample until the Oct 1, 2026 freeze): boards rebuilt as they stood before each of the last 127 events (3 years).

```json
{
 "snapshots": 127,
 "ranked_vs_ranked_bouts": 226,
 "ours_higher_ranked_win_rate": 0.544,
 "same_bouts_official_also_ranked": 204,
 "ours_on_same_bouts": 0.554,
 "official_on_same_bouts": 0.52,
 "predictive_elo_on_all_ranked_bouts": 0.624,
 "note": "Snapshots before the method freeze (v1.0) were rebuilt with today's rules, so they are an in-sample check; only bouts after the freeze date are a true forward test."
}
```

Agreement with public boards (UFC contenders only, champions removed; mean absolute gap in places among fighters both boards list, and share of one board's top 10 that appears in the other's top 10). External boards: UFC media panel and Meta UFC Rankings (ufc.com, Sept 26, 2026), Sherdog (Sept 14, 2026), Fight Matrix (Sept 20-27, 2026 for men's divisions, Aug-Sept for women's), ESPN (June 23, 2026 edition). Note: agreement is reported for context only; the design goal is a defensible board, not agreement.

| a            | b            |   shared |   mean_abs_gap |   top10_overlap_pct |
|:-------------|:-------------|---------:|---------------:|--------------------:|
| UFC media    | Meta         |      139 |           1.53 |               0.864 |
| UFC media    | Sherdog      |       83 |           0.88 |               0.736 |
| UFC media    | Fight Matrix |      120 |           1.37 |               0.855 |
| UFC media    | ESPN (Jun)   |       88 |           1.22 |               0.755 |
| UFC media    | Our board    |      121 |           1.76 |               0.818 |
| Meta         | Sherdog      |       82 |           1.38 |               0.709 |
| Meta         | Fight Matrix |      110 |           1.52 |               0.827 |
| Meta         | ESPN (Jun)   |       87 |           1.64 |               0.7   |
| Meta         | Our board    |      124 |           1.91 |               0.809 |
| Sherdog      | Fight Matrix |       83 |           1.16 |               0.908 |
| Sherdog      | ESPN (Jun)   |       75 |           0.92 |               0.862 |
| Sherdog      | Our board    |       78 |           1.62 |               0.874 |
| Fight Matrix | ESPN (Jun)   |       87 |           1.31 |               0.745 |
| Fight Matrix | Our board    |      106 |           1.81 |               0.773 |
| ESPN (Jun)   | Our board    |       81 |           1.84 |               0.784 |

Largest disagreements with the public consensus (36 flagged; type, our position, consensus median, and the model's reason):

| division             | fighter              | type                                  |   lab_full_position |   median_external | external_range   |   boards | reason                                                                    |
|:---------------------|:---------------------|:--------------------------------------|--------------------:|------------------:|:-----------------|---------:|:--------------------------------------------------------------------------|
| Heavyweight          | Tom Aspinall         | Consensus ranked, our board has #0    |                   0 |               1   | 1-2              |        5 | 337 days since last bout                                                  |
| Women's Flyweight    | Valentina Shevchenko | Consensus ranked, our board has #0    |                   0 |               1   | 1-1              |        3 | 316 days since last bout                                                  |
| Women's Bantamweight | Raquel Pennington    | Consensus ranked, ours outside top 15 |                 nan |               9.5 | 4-15             |        2 | Inactive: last UFC bout 2024-10-05 (721 days), outside the 540-day window |
| Light Heavyweight    | Alex Pereira         | Consensus ranked, ours outside top 15 |                   4 |               1   | 1-3              |        5 | Model places this fighter in Heavyweight (division of most recent bout)   |
| Lightweight          | King Green           | Our top 10, unranked on every board   |                   9 |             nan   | nan              |        0 | rating 1693, last five 4-1                                                |
| Middleweight         | Robert Whittaker     | Our top 10, unranked on every board   |                   5 |             nan   | nan              |        0 | rating 1723, last five 3-2                                                |
| Featherweight        | Steve Garcia         | Ours higher                           |                   5 |              10   | 7-13             |        5 | no quality wins                                                           |
| Bantamweight         | Marlon Vera          | Ours lower                            |                  52 |              11   | 10-14            |        3 | last five 1-4                                                             |
| Featherweight        | Patricio Pitbull     | Ours lower                            |                  47 |              11.5 | 9-14             |        2 | only 2 UFC bouts; no quality wins                                         |
| Featherweight        | Aaron Pico           | Ours lower                            |                  45 |              11   | 10-14            |        3 | only 2 UFC bouts; no quality wins                                         |
| Women's Strawweight  | Amanda Ribas         | Ours lower                            |                  44 |              11   | 9-13             |        2 | 428 days since last bout; last five 1-4                                   |
| Featherweight        | Brian Ortega         | Ours lower                            |                  39 |              10   | 7-13             |        2 | 400 days since last bout; last five 1-4                                   |
| Bantamweight         | Deiveson Figueiredo  | Ours lower                            |                  35 |               9   | 8-11             |        5 | last five 1-4                                                             |
| Flyweight            | Lone'er Kavanagh     | Ours lower                            |                  32 |               6   | 6-6              |        5 | rating 1476, last five 3-2                                                |
| Women's Strawweight  | Amanda Lemos         | Ours lower                            |                  35 |               9   | 5-15             |        5 | last five 1-4                                                             |
| Flyweight            | Steve Erceg          | Ours lower                            |                  30 |              10.5 | 9-12             |        2 | last five 2-3                                                             |
| Light Heavyweight    | Jan Błachowicz       | Ours lower                            |                  28 |               9   | 9-9              |        2 | last five 1-4                                                             |
| Middleweight         | Israel Adesanya      | Ours lower                            |                  26 |               9   | 8-11             |        4 | last five 1-4                                                             |
| Lightweight          | Salahdine Parnasse   | Ours lower                            |                  24 |               9   | 8-11             |        3 | only 1 UFC bouts                                                          |
| Women's Strawweight  | Angela Hill          | Ours lower                            |                  27 |              13.5 | 13-14            |        2 | last five 2-3                                                             |
| Featherweight        | Melquizael Costa     | Ours lower                            |                  25 |              12   | 12-12            |        2 | no quality wins                                                           |
| Lightweight          | Tom Nolan            | Ours lower                            |                  25 |              12.5 | 11-14            |        2 | no quality wins                                                           |
| Women's Strawweight  | Yan Xiaonan          | Ours lower                            |                  18 |               6   | 5-9              |        3 | last five 2-3                                                             |
| Women's Strawweight  | Tabatha Ricci        | Ours lower                            |                  21 |               9.5 | 8-12             |        4 | last five 2-3                                                             |
| Heavyweight          | Serghei Spivac       | Ours lower                            |                  20 |               9   | 7-13             |        4 | last five 2-3                                                             |
| Middleweight         | Abus Magomedov       | Ours lower                            |                  23 |              12.5 | 12-13            |        2 | no quality wins                                                           |
| Flyweight            | Sumudaerji           | Ours lower                            |                  22 |              12   | 11-13            |        2 | no quality wins                                                           |
| Light Heavyweight    | Jamahal Hill         | Ours lower                            |                  17 |               7   | 5-9              |        3 | 463 days since last bout; last five 2-3                                   |
| Women's Strawweight  | Mizuki               | Ours lower                            |                  22 |              12.5 | 10-15            |        2 | no quality wins; 337 days since last bout                                 |
| Bantamweight         | Aiemann Zahabi       | Ours lower                            |                  15 |               7.5 | 7-13             |        4 | rating 1585, last five 4-1                                                |
| Lightweight          | Mauricio Ruffy       | Ours lower                            |                  14 |               7   | 6-10             |        5 | rating 1612, last five 3-2                                                |
| Women's Bantamweight | Julianna Peña        | Ours lower                            |                   8 |               1   | 1-5              |        4 | 477 days since last bout                                                  |
| Bantamweight         | Farid Basharat       | Ours lower                            |                  16 |              11   | 9-13             |        2 | no quality wins                                                           |
| Light Heavyweight    | Khalil Rountree Jr.  | Ours lower                            |                   9 |               4   | 4-8              |        5 | 358 days since last bout                                                  |
| Welterweight         | Uroš Medić           | Ours lower                            |                  16 |              11   | 9-12             |        3 | no quality wins                                                           |
| Women's Bantamweight | Nora Cornolle        | Ours lower                            |                  17 |              12   | 10-13            |        3 | no quality wins; last five 2-3                                            |

## 7. Current boards (top 30 per division, with audit fields)

# Divisional boards as of 2026-09-26
weights: {'rating': 0.7, 'quality_wins': 0.3}; stability = 10th-90th percentile position across nearby weights


## Flyweight
 C. Joshua Van                 score +0.75  rating   1688  last5 5-0  ledger  6.0 (T10 4, T15 5 E)  days   8  band [0-0]
 1. Manel Kape                 score +0.74  rating   1717  last5 4-1  ledger  3.8 (T10 4, T15 4 E)  days  99  band [2-2]
 2. Kyoji Horiguchi            score +0.55  rating   1681  last5 4-1  ledger  1.9 (T10 2, T15 5 E)  days  99  band [5-5]
 3. Brandon Royval             score +0.39  rating   1602  last5 3-2  ledger  3.5 (T10 7, T15 8 E)  days  78  band [6-7]
 4. Alexandre Pantoja          score +0.75  rating   1700  last5 3-2  ledger  5.2 (T10 9, T15 9 E)  days   8  band [1-3]
 5. Tatsuro Taira              score +0.74  rating   1729  last5 3-2  ledger  3.0 (T10 2, T15 2)  days 141  band [1-3]
 6. Brandon Moreno             score +0.66  rating   1658  last5 3-2  ledger  5.8 (T10 10, T15 10 E)  days  15  band [4-4]
 7. Asu Almabayev              score +0.39  rating   1631  last5 4-1  ledger  1.5 (T10 2, T15 3)  days  92  band [6-7]
 8. Ramazan Temirov            score +0.22  rating   1574  last5 3-0  ledger  1.5 (T10 1, T15 2)  days  64  band [8-9]
 9. Kai Kara-France            score +0.22  rating   1602  last5 2-3  ledger  3.1 (T10 4, T15 5 E)  days 456  band [8-11]
10. Amir Albazi                score +0.16  rating   1591  last5 3-2  ledger -1.1 (T10 1, T15 1)  days 232  band [8-14]
11. Allan Nascimento           score +0.16  rating   1589  last5 4-1  ledger -1.0 (T10 0, T15 0)  days  99  band [10-13]
12. Tagir Ulanbekov            score +0.15  rating   1580  last5 4-1  ledger -0.5 (T10 0, T15 1)  days 309  band [11-12]
13. Alden Coria                score +0.15  rating   1571  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  71  band [10-13]
14. Tim Elliott                score +0.14  rating   1564  last5 3-2  ledger  0.1 (T10 1, T15 7 E)  days  15  band [12-14]
15. Andre Lima                 score +0.08  rating   1562  last5 4-1  ledger -1.0 (T10 0, T15 0)  days  29  band [15-16]
16. Bilal Hasan                score +0.07  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  29  band [15-19]
17. Rei Tsuruya                score +0.06  rating   1555  last5 3-1  ledger -1.0 (T10 0, T15 0)  days  29  band [17-18]
18. Imanol Rodriguez           score +0.05  rating   1536  last5 1-0  ledger  0.0 (T10 0, T15 0)  days 211  band [17-21]
19. Alessandro Costa           score +0.04  rating   1563  last5 4-1  ledger -2.0 (T10 0, T15 0)  days  78  band [16-20]
20. Jose Ochoa                 score +0.03  rating   1561  last5 2-2  ledger -2.0 (T10 0, T15 0)  days 141  band [18-21]
21. Edgar Chairez              score +0.01  rating   1552  last5 3-2  ledger -2.0 (T10 0, T15 0)  days  15  band [20-24]
22. Sumudaerji                 score +0.00  rating   1543  last5 4-1  ledger -1.5 (T10 0, T15 1)  days  29  band [22-24]
23. Jafel Filho                score -0.00  rating   1547  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 155  band [23-25]
24. Nyamjargal Tumendemberel   score -0.01  rating   1533  last5 2-1  ledger -1.0 (T10 0, T15 0)  days 204  band [22-25]
25. Fabia Sintes               score -0.01  rating   1518  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  22  band [19-27]
26. Alex Perez                 score -0.01  rating   1587  last5 2-3  ledger -1.4 (T10 2, T15 4)  days  29  band [22-26]
27. Joseph Morales             score -0.03  rating   1575  last5 2-3  ledger -1.0 (T10 0, T15 0)  days  15  band [26-27]
28. Lucas Rocha                score -0.10  rating   1502  last5 1-1  ledger -1.0 (T10 0, T15 0)  days 351  band [28-30]
29. HyunSung Park              score -0.10  rating   1515  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 344  band [29-31]
30. Steve Erceg                score -0.11  rating   1527  last5 2-3  ledger  0.6 (T10 2, T15 3)  days  64  band [28-31]

## Bantamweight
 C. Petr Yan                   score +1.21  rating   1748  last5 4-1  ledger  7.1 (T10 7, T15 10 E)  days 295 (injury layoff)  band [0-0]
 1. Merab Dvalishvili          score +1.48  rating   1786  last5 4-1  ledger  9.6 (T10 8, T15 11 E)  days 295  band [1-1]
 2. Sean O'Malley              score +1.09  rating   1729  last5 3-2  ledger  6.1 (T10 5, T15 5 E)  days 105  band [3-3]
 3. Song Yadong                score +1.23  rating   1777  last5 3-2  ledger  6.0 (T10 5, T15 8 E)  days  29  band [2-2]
 4. Umar Nurmagomedov          score +0.91  rating   1723  last5 3-2  ledger  3.6 (T10 3, T15 3)  days  29  band [4-4]
 5. Mario Bautista             score +0.71  rating   1681  last5 4-1  ledger  2.6 (T10 2, T15 4)  days  78  band [5-6]
 6. Cory Sandhagen             score +0.71  rating   1733  last5 2-3  ledger  2.3 (T10 8, T15 8 E)  days  78  band [5-6]
 7. Raul Rosas Jr.             score +0.53  rating   1656  last5 5-0  ledger  1.0 (T10 0, T15 2)  days   1  band [7-8]
 8. Raoni Barcelos             score +0.33  rating   1612  last5 4-1  ledger  0.0 (T10 0, T15 1)  days   1  band [14-16]
 9. Montel Jackson             score +0.55  rating   1714  last5 3-2  ledger -1.6 (T10 0, T15 0)  days   1  band [7-10]
10. David Martinez             score +0.49  rating   1619  last5 4-0  ledger  2.2 (T10 2, T15 2)  days  15  band [7-10]
11. Marcus McGhee              score +0.49  rating   1644  last5 4-1  ledger  1.0 (T10 0, T15 1)  days 113  band [9-10]
12. Jose Aldo                  score +0.41  rating   1652  last5 2-3  ledger  1.8 (T10 11, T15 13 E)  days 505  band [11-13]
13. Brady Hiestand             score +0.40  rating   1634  last5 4-1  ledger  0.0 (T10 0, T15 0)  days   1  band [11-12]
14. Payton Talbott             score +0.39  rating   1633  last5 4-1  ledger  0.0 (T10 1, T15 1)  days 295  band [12-14]
15. Aiemann Zahabi             score +0.34  rating   1585  last5 4-1  ledger  1.5 (T10 1, T15 2)  days 105  band [12-18]
16. Farid Basharat             score +0.33  rating   1608  last5 5-0  ledger  0.2 (T10 0, T15 0)  days  78  band [14-17]
17. Vinicius Oliveira          score +0.33  rating   1612  last5 4-1  ledger  0.0 (T10 0, T15 1)  days  99  band [15-17]
18. Bryce Mitchell             score +0.29  rating   1621  last5 3-2  ledger -1.0 (T10 1, T15 2)  days 113  band [16-19]
19. Elijah Smith               score +0.25  rating   1587  last5 3-0  ledger  0.0 (T10 0, T15 0)  days 197  band [18-21]
20. Daniel Marcos              score +0.25  rating   1607  last5 4-1  ledger -1.0 (T10 0, T15 0)  days 323  band [19-21]
21. Cody Haddon                score +0.23  rating   1580  last5 2-0  ledger  0.0 (T10 0, T15 0)  days 120  band [20-24]
22. Davey Grant                score +0.21  rating   1593  last5 3-2  ledger -0.8 (T10 0, T15 0)  days 155  band [22-23]
23. Chris Gutierrez            score +0.21  rating   1608  last5 3-2  ledger -1.7 (T10 0, T15 1)  days 358  band [20-26]
24. Rob Font                   score +0.20  rating   1630  last5 2-3  ledger -0.6 (T10 4, T15 6 E)  days 204  band [23-25]
25. Ethyn Ewing                score +0.19  rating   1568  last5 2-0  ledger  0.0 (T10 0, T15 0)  days 176  band [22-28]
26. Jakub Wiklacz              score +0.13  rating   1551  last5 2-0  ledger  0.0 (T10 0, T15 0)  days 232  band [25-32]
27. Juan Diaz                  score +0.13  rating   1550  last5 1-0  ledger  0.0 (T10 0, T15 0)  days 134  band [27-33]
28. Da'Mon Blackshear          score +0.13  rating   1589  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 428  band [27-34]
29. Said Nurmagomedov          score +0.12  rating   1635  last5 2-3  ledger -2.0 (T10 0, T15 0)  days 428  band [25-37]
30. Aleksandre Topuria         score +0.12  rating   1546  last5 2-0  ledger  0.0 (T10 0, T15 0)  days 309  band [28-34]

## Featherweight
 C. Alexander Volkanovski      score +1.56  rating   1835  last5 3-2  ledger  7.4 (T10 11, T15 11 E)  days 239  band [0-0]
 1. Aljamain Sterling          score +1.58  rating   1805  last5 3-2  ledger  8.8 (T10 12, T15 14 E)  days 155  band [1-1]
 2. Movsar Evloev              score +0.88  rating   1677  last5 5-0  ledger  4.8 (T10 4, T15 5 E)  days 190  band [2-3]
 3. Diego Lopes                score +0.79  rating   1706  last5 3-2  ledger  2.5 (T10 3, T15 5 E)  days 105  band [2-3]
 4. Jean Silva                 score +0.69  rating   1716  last5 4-1  ledger  0.8 (T10 1, T15 2)  days  15  band [4-7]
 5. Steve Garcia               score +0.68  rating   1693  last5 4-1  ledger  1.5 (T10 0, T15 2)  days 105  band [4-5]
 6. Lerone Murphy              score +0.66  rating   1674  last5 4-1  ledger  2.0 (T10 1, T15 3)  days 190  band [5-6]
 7. Yair Rodriguez             score +0.63  rating   1653  last5 3-2  ledger  2.5 (T10 4, T15 4 E)  days 533  band [6-7]
 8. Kevin Vallejos             score +0.53  rating   1657  last5 4-0  ledger  1.0 (T10 0, T15 2)  days 197  band [8-8]
 9. Arnold Allen               score +0.51  rating   1694  last5 2-3  ledger  1.2 (T10 3, T15 5 E)  days 134  band [9-10]
10. Youssef Zalal              score +0.51  rating   1649  last5 4-1  ledger  1.0 (T10 2, T15 2)  days 155  band [9-11]
11. Pat Sabatini               score +0.37  rating   1655  last5 4-1  ledger -1.0 (T10 0, T15 0)  days 141  band [12-14]
12. Joanderson Brito           score +0.42  rating   1683  last5 3-2  ledger -1.6 (T10 0, T15 0)  days   8  band [10-12]
13. Cub Swanson                score +0.41  rating   1645  last5 3-2  ledger -0.2 (T10 4, T15 8 E)  days 169  band [11-13]
14. Luke Riley                 score +0.33  rating   1616  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  78  band [13-14]
15. Mairon Santos              score +0.30  rating   1608  last5 4-0  ledger  0.0 (T10 0, T15 0)  days 295  band [15-16]
16. Tommy McMillen             score +0.28  rating   1601  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  15  band [16-17]
17. Chepe Mariscal             score +0.28  rating   1617  last5 4-1  ledger -0.8 (T10 0, T15 0)  days 316  band [15-17]
18. Felipe Lima                score +0.23  rating   1609  last5 3-1  ledger -1.0 (T10 0, T15 0)  days  22  band [18-19]
19. Jamall Emmers              score +0.22  rating   1607  last5 4-1  ledger -1.0 (T10 0, T15 0)  days  36  band [19-21]
20. Marcio Barbosa             score +0.22  rating   1582  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  36  band [18-23]
21. David Onama                score +0.20  rating   1588  last5 4-1  ledger -0.5 (T10 0, T15 1)  days 330  band [20-22]
22. Yadier del Valle           score +0.19  rating   1591  last5 3-1  ledger -0.8 (T10 0, T15 0)  days  50  band [21-22]
23. Dooho Choi                 score +0.16  rating   1584  last5 3-2  ledger -1.0 (T10 0, T15 0)  days   8  band [25-26]
24. Daniel Santos              score +0.17  rating   1589  last5 4-1  ledger -1.0 (T10 0, T15 0)  days 134  band [23-24]
25. Melquizael Costa           score +0.17  rating   1588  last5 4-1  ledger -1.0 (T10 0, T15 1)  days 134  band [24-25]
26. Pavel Andrusca             score +0.13  rating   1544  last5 1-0  ledger  0.2 (T10 0, T15 0)  days  22  band [23-29]
27. Nathaniel Wood             score +0.16  rating   1606  last5 4-1  ledger -1.9 (T10 0, T15 0)  days  22  band [20-32]
28. Sean Woodson               score +0.12  rating   1566  last5 4-1  ledger -0.8 (T10 0, T15 0)  days  29  band [27-32]
29. Keiichiro Nakamura         score +0.11  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days 239  band [27-31]
30. Sean King III              score +0.11  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  15  band [29-33]

## Lightweight
 C. Justin Gaethje             score +1.26  rating   1740  last5 4-1  ledger  8.3 (T10 10, T15 11 E)  days 105  band [0-0]
 1. Charles Oliveira           score +1.50  rating   1860  last5 3-2  ledger  7.1 (T10 12, T15 12 E)  days 204  band [2-2]
 2. Max Holloway               score +1.56  rating   1872  last5 3-2  ledger  7.4 (T10 15, T15 15 E)  days  78  band [1-1]
 3. Ilia Topuria               score +1.27  rating   1792  last5 4-1  ledger  6.5 (T10 5, T15 5 E)  days 105  band [3-3]
 4. Arman Tsarukyan            score +1.14  rating   1780  last5 5-0  ledger  5.3 (T10 4, T15 5 E)  days   8  band [4-4]
 5. Paddy Pimblett             score +0.74  rating   1720  last5 4-1  ledger  2.2 (T10 2, T15 3)  days  78  band [5-5]
 6. Renato Moicano             score +0.58  rating   1695  last5 3-2  ledger  1.0 (T10 3, T15 6 E)  days 176  band [8-9]
 7. Benoit Saint Denis         score +0.64  rating   1702  last5 4-1  ledger  1.5 (T10 2, T15 4)  days  78  band [6-7]
 8. Quillan Salkilld           score +0.63  rating   1693  last5 5-0  ledger  1.8 (T10 1, T15 2)  days  50  band [6-7]
 9. King Green                 score +0.42  rating   1693  last5 4-1  ledger -1.0 (T10 2, T15 2)  days  78  band [10-11]
10. Grant Dawson               score +0.50  rating   1730  last5 4-1  ledger -1.4 (T10 0, T15 1)  days 141  band [8-10]
11. Mateusz Gamrot             score +0.45  rating   1708  last5 2-3  ledger  0.8 (T10 2, T15 5 E)  days  50  band [9-11]
12. Jim Miller                 score +0.36  rating   1679  last5 3-2  ledger -1.3 (T10 1, T15 1)  days 141  band [12-14]
13. Chris Padilla              score +0.33  rating   1627  last5 5-0  ledger  0.2 (T10 0, T15 0)  days  36  band [12-13]
14. Mauricio Ruffy             score +0.25  rating   1612  last5 3-2  ledger -0.2 (T10 1, T15 2)  days   8  band [16-16]
15. Rafael Fiziev              score +0.28  rating   1634  last5 2-3  ledger  1.3 (T10 1, T15 3)  days  92  band [13-17]
16. Jalin Turner               score +0.28  rating   1640  last5 3-2  ledger -0.9 (T10 0, T15 2)  days  43  band [14-17]
17. Tommy Gantt                score +0.23  rating   1593  last5 2-0  ledger  0.2 (T10 0, T15 0)  days  15  band [15-20]
18. MarQuel Mederos            score +0.22  rating   1594  last5 4-0  ledger  0.0 (T10 0, T15 0)  days  36  band [18-21]
19. Nurullo Aliev              score +0.21  rating   1593  last5 4-0  ledger  0.0 (T10 0, T15 0)  days  64  band [19-22]
20. Ignacio Bahamondes         score +0.21  rating   1626  last5 3-2  ledger -1.2 (T10 0, T15 1)  days  15  band [15-21]
21. Manuel Torres              score +0.18  rating   1613  last5 3-2  ledger -1.2 (T10 0, T15 1)  days  92  band [19-23]
22. Axel Sola                  score +0.16  rating   1594  last5 3-1  ledger -0.8 (T10 0, T15 0)  days  22  band [22-23]
23. Diego Ferreira             score +0.16  rating   1620  last5 3-2  ledger -1.8 (T10 0, T15 1)  days  50  band [18-27]
24. Salahdine Parnasse         score +0.14  rating   1541  last5 1-0  ledger  1.0 (T10 1, T15 1)  days  22  band [20-30]
25. Tom Nolan                  score +0.13  rating   1575  last5 5-0  ledger -0.5 (T10 0, T15 1)  days 113  band [24-26]
26. Rafa Garcia                score +0.10  rating   1590  last5 3-2  ledger -1.4 (T10 0, T15 0)  days  15  band [25-29]
27. Chase Hooper               score +0.10  rating   1600  last5 3-2  ledger -1.8 (T10 0, T15 0)  days  71  band [24-30]
28. Manoel Sousa               score +0.08  rating   1547  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  50  band [25-31]
29. Noah Gugnon                score +0.08  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  57  band [26-35]
30. Esteban Ribovics           score +0.07  rating   1589  last5 3-2  ledger -1.8 (T10 0, T15 0)  days  43  band [27-32]

## Welterweight
 C. Islam Makhachev            score +1.59  rating   1883  last5 5-0  ledger 11.2 (T10 8, T15 9 E)  days  43  band [0-0]
 1. Michael Morales            score +0.67  rating   1708  last5 5-0  ledger  3.2 (T10 2, T15 3)  days 316  band [4-4]
 2. Sean Brady                 score +0.77  rating   1736  last5 4-1  ledger  3.8 (T10 4, T15 5 E)  days 141  band [1-1]
 3. Carlos Prates              score +0.76  rating   1739  last5 4-1  ledger  3.2 (T10 2, T15 4)  days 148  band [2-3]
 4. Ian Machado Garry          score +0.75  rating   1729  last5 3-2  ledger  3.6 (T10 2, T15 6 E)  days  43  band [2-3]
 5. Jack Della Maddalena       score +0.53  rating   1665  last5 3-2  ledger  3.0 (T10 2, T15 3)  days 148  band [6-9]
 6. Gabriel Bonfim             score +0.49  rating   1682  last5 5-0  ledger  1.2 (T10 1, T15 2)  days 113  band [7-9]
 7. Belal Muhammad             score +0.55  rating   1710  last5 2-3  ledger  3.7 (T10 6, T15 6 E)  days 113  band [5-6]
 8. Leon Edwards               score +0.52  rating   1705  last5 2-3  ledger  3.6 (T10 4, T15 7 E)  days 316  band [7-8]
 9. Joaquin Buckley            score +0.50  rating   1696  last5 3-2  ledger  0.8 (T10 2, T15 3)  days 141  band [5-9]
10. Kamaru Usman               score +0.42  rating   1812  last5 1-4  ledger  4.2 (T10 9, T15 9 E)  days  71  band [10-10]
11. Daniil Donchenko           score +0.34  rating   1649  last5 4-0  ledger  0.2 (T10 0, T15 0)  days  22  band [11-11]
12. Rinat Fakhretdinov         score +0.32  rating   1640  last5 5-0  ledger  0.4 (T10 0, T15 0)  days 386  band [12-12]
13. Mike Malott                score +0.29  rating   1637  last5 4-1  ledger  0.0 (T10 0, T15 2)  days 162  band [13-14]
14. Yaroslav Amosov            score +0.24  rating   1609  last5 2-0  ledger  0.5 (T10 0, T15 0)  days 141  band [15-23]
15. Neil Magny                 score +0.29  rating   1651  last5 3-2  ledger -0.9 (T10 3, T15 7 E)  days  43  band [12-14]
16. Uros Medic                 score +0.25  rating   1631  last5 4-1  ledger -0.5 (T10 0, T15 2)  days  57  band [17-18]
17. Daniel Rodriguez           score +0.26  rating   1635  last5 3-2  ledger -0.5 (T10 0, T15 3)  days  57  band [15-17]
18. Jeremiah Wells             score +0.26  rating   1638  last5 3-2  ledger -0.8 (T10 0, T15 0)  days  43  band [16-18]
19. Sam Patterson              score +0.23  rating   1628  last5 4-1  ledger -0.8 (T10 0, T15 0)  days  64  band [18-21]
20. Jacobe Smith               score +0.22  rating   1611  last5 3-0  ledger  0.0 (T10 0, T15 0)  days 218  band [19-24]
21. Myktybek Orolbai           score +0.20  rating   1637  last5 3-2  ledger -1.8 (T10 0, T15 0)  days  43  band [20-22]
22. Jake Matthews              score +0.20  rating   1640  last5 4-1  ledger -1.9 (T10 0, T15 0)  days 120  band [19-23]
23. Joel Alvarez               score +0.20  rating   1626  last5 3-2  ledger -1.2 (T10 0, T15 1)  days  43  band [21-24]
24. Kevin Holland              score +0.19  rating   1659  last5 3-2  ledger -3.2 (T10 0, T15 2)  days 169  band [15-26]
25. Ty Miller                  score +0.11  rating   1576  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  50  band [24-26]
26. Jonathan Micallef          score +0.10  rating   1573  last5 3-0  ledger  0.0 (T10 0, T15 0)  days 148  band [25-28]
27. Jean-Paul Lebosnoyani      score -0.01  rating   1535  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  71  band [32-37]
28. Seokhyeon Ko               score +0.08  rating   1583  last5 2-1  ledger -1.0 (T10 0, T15 0)  days  71  band [27-28]
29. Khaos Williams             score +0.08  rating   1599  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 134  band [25-31]
30. Levan Chokheli             score +0.02  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  99  band [28-32]

## Middleweight
 C. Sean Strickland            score +0.97  rating   1753  last5 3-2  ledger  6.3 (T10 6, T15 7 E)  days 141  band [0-0]
 1. Khamzat Chimaev            score +0.99  rating   1759  last5 4-1  ledger  6.3 (T10 4, T15 5 E)  days 141  band [2-2]
 2. Dricus Du Plessis          score +1.14  rating   1782  last5 4-1  ledger  7.7 (T10 7, T15 8 E)  days  71  band [1-1]
 3. Nassourdine Imavov         score +0.90  rating   1725  last5 5-0  ledger  6.3 (T10 5, T15 6 E)  days 386  band [3-3]
 4. Brendan Allen              score +0.78  rating   1731  last5 3-2  ledger  3.8 (T10 2, T15 5 E)  days 113  band [4-4]
 5. Robert Whittaker           score +0.71  rating   1723  last5 3-2  ledger  3.0 (T10 9, T15 12 E)  days  78  band [5-5]
 6. Joe Pyfer                  score +0.57  rating   1717  last5 4-1  ledger  0.9 (T10 1, T15 1)  days 183  band [6-6]
 7. Gregory Rodrigues          score +0.55  rating   1708  last5 4-1  ledger  1.0 (T10 1, T15 2)  days  36  band [7-8]
 8. Anthony Hernandez          score +0.54  rating   1694  last5 3-2  ledger  1.5 (T10 2, T15 3)  days  36  band [7-8]
 9. Caio Borralho              score +0.49  rating   1665  last5 4-1  ledger  2.0 (T10 2, T15 3)  days 204  band [9-9]
10. Christian Leroy Duncan     score +0.40  rating   1671  last5 5-0  ledger  0.2 (T10 0, T15 2)  days  71  band [10-10]
11. Yousri Belgaroui           score +0.28  rating   1632  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  15  band [11-12]
12. Ateba Gautier              score +0.28  rating   1632  last5 5-0  ledger  0.0 (T10 0, T15 0)  days 141  band [12-13]
13. Ikram Aliskerov            score +0.27  rating   1638  last5 4-1  ledger -0.5 (T10 0, T15 0)  days  92  band [11-14]
14. Michael Page               score +0.25  rating   1602  last5 4-1  ledger  1.0 (T10 1, T15 3)  days  22  band [11-18]
15. Bo Nickal                  score +0.25  rating   1636  last5 4-1  ledger -0.8 (T10 0, T15 0)  days 105  band [14-17]
16. Cam Rowston                score +0.24  rating   1613  last5 3-0  ledger  0.2 (T10 0, T15 0)  days 148  band [15-16]
17. Baisangur Susurkaev        score +0.23  rating   1615  last5 3-0  ledger  0.0 (T10 0, T15 0)  days 141  band [16-17]
18. Shara Magomedov            score +0.22  rating   1621  last5 4-1  ledger -0.5 (T10 0, T15 0)  days  92  band [15-20]
19. Jacob Malkoun              score +0.22  rating   1611  last5 4-1  ledger  0.0 (T10 0, T15 0)  days 148  band [18-20]
20. Edmen Shahbazyan           score +0.22  rating   1612  last5 4-1  ledger -0.1 (T10 0, T15 1)  days   8  band [19-20]
21. Ryan Gandra                score +0.17  rating   1592  last5 3-0  ledger  0.0 (T10 0, T15 0)  days   8  band [21-23]
22. Ismail Naurdiev            score +0.17  rating   1605  last5 3-2  ledger -0.7 (T10 0, T15 0)  days 309  band [21-23]
23. Abus Magomedov             score +0.16  rating   1610  last5 4-1  ledger -1.0 (T10 0, T15 1)  days  92  band [21-25]
24. Damian Pinas               score +0.13  rating   1577  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  78  band [24-26]
25. Donte Johnson              score +0.10  rating   1568  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  43  band [25-28]
26. Israel Adesanya            score +0.09  rating   1675  last5 1-4  ledger  5.1 (T10 10, T15 11 E)  days 183  band [22-31]
27. Nursulton Ruziboev         score +0.08  rating   1600  last5 3-2  ledger -2.0 (T10 0, T15 0)  days  22  band [24-30]
28. Roman Dolidze              score +0.07  rating   1630  last5 2-3  ledger -0.9 (T10 3, T15 4)  days  36  band [26-28]
29. Vicente Luque              score +0.03  rating   1645  last5 2-3  ledger -2.4 (T10 3, T15 3)  days  43  band [25-34]
30. Cezary Oleksiejczuk        score +0.03  rating   1544  last5 1-0  ledger  0.0 (T10 0, T15 0)  days 288  band [27-32]

## Light Heavyweight
 C. Carlos Ulberg              score +0.83  rating   1712  last5 5-0  ledger  5.5 (T10 4, T15 5 E)  days 169  band [0-0]
 1. Magomed Ankalaev           score +1.00  rating   1739  last5 4-1  ledger  7.2 (T10 8, T15 8 E)  days  64  band [1-1]
 2. Paulo Costa                score +0.73  rating   1725  last5 3-2  ledger  2.8 (T10 3, T15 4)  days 169  band [3-3]
 3. Navajo Stirling            score +0.51  rating   1673  last5 5-0  ledger  1.5 (T10 1, T15 1)  days  57  band [4-5]
 4. Jiri Prochazka             score +0.83  rating   1730  last5 3-2  ledger  4.5 (T10 6, T15 6 E)  days 169  band [2-2]
 5. Dominick Reyes             score +0.49  rating   1661  last5 4-1  ledger  1.9 (T10 4, T15 6 E)  days 169  band [5-6]
 6. Volkan Oezdemir            score +0.47  rating   1637  last5 3-2  ledger  2.8 (T10 7, T15 8 E)  days 309  band [4-7]
 7. Azamat Murzakanov          score +0.46  rating   1668  last5 4-1  ledger  0.8 (T10 1, T15 3)  days 169  band [6-9]
 8. Bogdan Guskov              score +0.44  rating   1641  last5 4-1  ledger  2.0 (T10 1, T15 2)  days  64  band [8-8]
 9. Khalil Rountree Jr.        score +0.43  rating   1619  last5 3-2  ledger  3.1 (T10 2, T15 4)  days 358  band [7-9]
10. Reinier de Ridder          score +0.34  rating   1632  last5 3-2  ledger  0.5 (T10 1, T15 2)  days  36  band [10-10]
11. Abdul Rakhman Yakhyaev     score +0.26  rating   1614  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  92  band [11-11]
12. Johnny Walker              score +0.14  rating   1634  last5 2-3  ledger -0.4 (T10 2, T15 5 E)  days 169  band [12-14]
13. Alonzo Menifield           score +0.04  rating   1580  last5 4-1  ledger -2.1 (T10 0, T15 2)  days   8  band [16-23]
14. Iwo Baraniewski            score +0.13  rating   1590  last5 3-1  ledger -1.0 (T10 0, T15 0)  days   8  band [13-14]
15. Muhammad Saidov            score +0.12  rating   1561  last5 1-0  ledger  0.2 (T10 0, T15 0)  days  64  band [12-16]
16. Nikita Krylov              score +0.07  rating   1621  last5 2-3  ledger -1.0 (T10 3, T15 4)  days  78  band [14-21]
17. Jamahal Hill               score +0.05  rating   1586  last5 2-3  ledger  0.5 (T10 3, T15 5 E)  days 463  band [15-20]
18. Billy Elekana              score +0.05  rating   1562  last5 3-1  ledger -1.0 (T10 0, T15 0)  days 239  band [17-20]
19. Jimmy Crute                score +0.05  rating   1592  last5 2-3  ledger  0.1 (T10 0, T15 0)  days 365  band [18-20]
20. Lucas Fernando             score +0.04  rating   1540  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  43  band [16-22]
21. Liu Ce                     score +0.04  rating   1539  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  29  band [17-23]
22. Dustin Jacoby              score +0.03  rating   1592  last5 3-2  ledger -3.0 (T10 0, T15 0)  days  64  band [15-26]
23. Modestas Bukauskas         score -0.03  rating   1552  last5 4-1  ledger -2.0 (T10 0, T15 0)  days  22  band [24-28]
24. Christian Edwards          score +0.03  rating   1554  last5 1-1  ledger -1.0 (T10 0, T15 0)  days   1  band [21-23]
25. Luis Hernandez             score +0.01  rating   1530  last5 1-0  ledger  0.0 (T10 0, T15 0)  days   1  band [20-27]
26. Felipe Franco              score -0.00  rating   1543  last5 1-1  ledger -1.0 (T10 0, T15 0)  days  71  band [24-25]
27. Zhang Mingyang             score -0.02  rating   1546  last5 3-2  ledger -1.5 (T10 0, T15 1)  days 120  band [26-26]
28. Jan Blachowicz             score -0.05  rating   1685  last5 1-4  ledger  1.5 (T10 6, T15 7 E)  days  57  band [28-30]
29. Magomed Tuchalov           score -0.07  rating   1503  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  64  band [25-30]
30. Uran Satybaldiev           score -0.08  rating   1518  last5 1-1  ledger -1.0 (T10 0, T15 0)  days 400  band [29-30]

## Heavyweight
IC. Ciryl Gane                 score +1.10  rating   1812  last5 4-1  ledger  6.2 (T10 8, T15 8 E)  days 105  band [0-0]
 R. Tom Aspinall               score +0.87  rating   1754  last5 4-1  ledger  4.4 (T10 4, T15 5 E)  days 337 (injury layoff)  band [0-0]
 1. Alexander Volkov           score +1.11  rating   1784  last5 4-1  ledger  8.1 (T10 10, T15 11 E)  days 141  band [2-2]
 2. Josh Hokit                 score +0.53  rating   1660  last5 4-0  ledger  2.5 (T10 2, T15 2)  days 105  band [6-6]
 3. Curtis Blaydes             score +0.82  rating   1730  last5 3-2  ledger  4.7 (T10 12, T15 13 E)  days  15  band [3-3]
 4. Alex Pereira               score +1.18  rating   1789  last5 3-2  ledger  9.5 (T10 8, T15 8 E)  days 105  band [1-1]
 5. Waldo Cortes Acosta        score +0.71  rating   1709  last5 3-2  ledger  3.5 (T10 3, T15 4)  days  15  band [4-4]
 6. Sergei Pavlovich           score +0.68  rating   1690  last5 3-2  ledger  3.9 (T10 6, T15 8 E)  days 120  band [5-5]
 7. Valter Walker              score +0.37  rating   1645  last5 5-0  ledger -0.2 (T10 0, T15 1)  days  64  band [7-9]
 8. Rizvan Kuniev              score +0.37  rating   1599  last5 2-1  ledger  2.5 (T10 2, T15 2)  days  64  band [7-10]
 9. Mario Pinto                score +0.35  rating   1629  last5 4-0  ledger  0.2 (T10 0, T15 0)  days  22  band [8-10]
10. Derrick Lewis              score +0.34  rating   1624  last5 2-3  ledger  3.9 (T10 9, T15 14 E)  days 105  band [8-12]
11. Brando Pericic             score +0.34  rating   1622  last5 3-0  ledger  0.5 (T10 0, T15 1)  days 148  band [9-11]
12. Vitor Petrino              score +0.28  rating   1623  last5 4-1  ledger -1.0 (T10 1, T15 1)  days  36  band [11-12]
13. Gokhan Saricam             score +0.14  rating   1557  last5 1-0  ledger  0.0 (T10 0, T15 0)  days 162  band [13-13]
14. Jovan Leka                 score +0.11  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  57  band [14-14]
15. Anthony Wint               score +0.11  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  36  band [15-15]
16. RJ Harris                  score +0.11  rating   1544  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  71  band [16-16]
17. Jose Montanha              score +0.10  rating   1542  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  50  band [17-17]
18. Steven Asplund             score +0.06  rating   1543  last5 2-1  ledger -1.0 (T10 0, T15 0)  days  50  band [18-19]
19. Ryan Spann                 score +0.04  rating   1551  last5 3-2  ledger -1.9 (T10 1, T15 2)  days  22  band [18-20]
20. Serghei Spivac             score +0.02  rating   1565  last5 2-3  ledger  0.2 (T10 3, T15 6 E)  days  36  band [19-22]
21. Shamil Gaziev              score +0.00  rating   1549  last5 3-2  ledger -2.8 (T10 0, T15 0)  days  36  band [20-26]
22. Hamdy Abdelwahab           score +0.00  rating   1520  last5 2-2  ledger -1.0 (T10 0, T15 0)  days 337  band [21-23]
23. Tyrell Fortune             score -0.06  rating   1482  last5 1-1  ledger  0.0 (T10 1, T15 1)  days  64  band [23-30]
24. Marcin Tybura              score -0.01  rating   1575  last5 2-3  ledger -1.1 (T10 3, T15 7 E)  days  57  band [21-24]
25. Martin Buday               score -0.02  rating   1508  last5 4-1  ledger -0.8 (T10 0, T15 0)  days 428  band [22-25]
26. Ante Delija                score -0.04  rating   1506  last5 1-2  ledger -1.0 (T10 1, T15 1)  days 218  band [25-26]
27. Tanner Boser               score -0.04  rating   1560  last5 2-3  ledger -0.9 (T10 0, T15 0)  days 162  band [24-28]
28. Tallison Teixeira          score -0.06  rating   1505  last5 2-2  ledger -1.5 (T10 0, T15 1)  days 120  band [27-29]
29. Gable Steveson             score -0.06  rating   1497  last5 1-1  ledger -1.0 (T10 0, T15 0)  days   8  band [27-29]
30. Denzel Freeman             score -0.12  rating   1476  last5 1-1  ledger -1.0 (T10 0, T15 0)  days 246  band [31-35]

## Women's Strawweight
 C. Mackenzie Dern             score +0.71  rating   1651  last5 4-1  ledger  7.0 (T10 6, T15 8 E)  days  43  band [0-0]
 1. Zhang Weili                score +0.86  rating   1730  last5 4-1  ledger  5.6 (T10 7, T15 7 E)  days 316  band [1-1]
 2. Virna Jandiroba            score +0.73  rating   1669  last5 4-1  ledger  6.3 (T10 5, T15 7 E)  days 176  band [2-3]
 3. Tatiana Suarez             score +0.72  rating   1720  last5 4-1  ledger  3.4 (T10 6, T15 6 E)  days 169  band [2-3]
 4. Gillian Robertson          score +0.47  rating   1650  last5 4-1  ledger  2.5 (T10 2, T15 4)  days  43  band [4-4]
 5. Iasmin Lucindo             score +0.36  rating   1609  last5 4-1  ledger  2.5 (T10 1, T15 3)  days 414  band [5-8]
 6. Fatima Kline               score +0.36  rating   1645  last5 4-1  ledger  0.5 (T10 1, T15 2)  days  71  band [5-8]
 7. Denise Gomes               score +0.35  rating   1629  last5 5-0  ledger  1.2 (T10 1, T15 2)  days  29  band [6-7]
 8. Alexia Thainara            score +0.34  rating   1622  last5 4-0  ledger  1.5 (T10 1, T15 2)  days  50  band [6-8]
 9. Loopy Godinez              score +0.24  rating   1614  last5 2-3  ledger  2.8 (T10 2, T15 3)  days 169  band [9-10]
10. Jessica Andrade            score +0.21  rating   1589  last5 2-3  ledger  3.6 (T10 12, T15 13 E)  days 407  band [10-12]
11. Jaqueline Amorim           score +0.20  rating   1618  last5 4-1  ledger -1.0 (T10 0, T15 0)  days 120  band [9-11]
12. Stephanie Luciano          score +0.16  rating   1602  last5 3-1  ledger -1.0 (T10 0, T15 0)  days  57  band [11-12]
13. Shanelle Dyer              score +0.11  rating   1567  last5 2-0  ledger  0.0 (T10 0, T15 0)  days  36  band [13-13]
14. Tecia Pennington           score +0.07  rating   1616  last5 2-3  ledger -0.4 (T10 1, T15 4)  days 323  band [14-16]
15. Piera Rodriguez            score +0.05  rating   1564  last5 3-2  ledger -1.0 (T10 0, T15 0)  days 197  band [15-18]
16. Delphine Benouaich         score +0.05  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  22  band [14-19]
17. Tina Black                 score +0.05  rating   1545  last5 1-0  ledger  0.0 (T10 0, T15 0)  days   1  band [15-20]
18. Yan Xiaonan                score +0.05  rating   1589  last5 2-3  ledger  0.4 (T10 4, T15 5 E)  days  29  band [16-18]
19. Talita Alencar             score +0.01  rating   1549  last5 4-1  ledger -1.0 (T10 0, T15 0)  days 155  band [19-21]
20. Alice Ardelean             score +0.01  rating   1567  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 134  band [17-23]
21. Tabatha Ricci              score -0.00  rating   1581  last5 2-3  ledger -0.1 (T10 2, T15 2)  days  71  band [21-22]
22. Mizuki                     score -0.02  rating   1520  last5 3-1  ledger  0.0 (T10 0, T15 0)  days 337  band [19-24]
23. Julia Polastri             score -0.02  rating   1576  last5 3-2  ledger -3.0 (T10 0, T15 0)  days  29  band [16-26]
24. Carol Foro                 score -0.03  rating   1516  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  50  band [21-26]
25. Ketlen Souza               score -0.05  rating   1547  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 113  band [23-26]
26. Yazmin Jauregui            score -0.05  rating   1529  last5 3-2  ledger -1.0 (T10 0, T15 0)  days   1  band [24-26]
27. Angela Hill                score -0.10  rating   1574  last5 2-3  ledger -1.6 (T10 1, T15 3)  days 120  band [27-28]
28. Shi Ming                   score -0.12  rating   1503  last5 1-1  ledger -1.0 (T10 0, T15 0)  days 400  band [27-29]
29. Sam Hughes                 score -0.14  rating   1513  last5 3-2  ledger -2.0 (T10 0, T15 0)  days 197  band [28-30]
30. Gigi Canuto                score -0.17  rating   1484  last5 0-1  ledger -1.0 (T10 0, T15 0)  days  50  band [29-31]

## Women's Flyweight   (title vacant)
 R. Valentina Shevchenko       score +1.17  rating   1769  last5 4-1  ledger  9.8 (T10 14, T15 14 E)  days 316 (injury layoff)  band [0-0]
 1. Alexa Grasso               score +0.59  rating   1652  last5 3-2  ledger  4.4 (T10 8, T15 9 E)  days  15  band [5-5]
 2. Manon Fiorot               score +0.82  rating   1711  last5 3-2  ledger  5.7 (T10 5, T15 5 E)  days  15  band [1-2]
 3. Natalia Silva              score +0.73  rating   1695  last5 5-0  ledger  4.8 (T10 4, T15 5 E)  days 246  band [3-4]
 4. Rose Namajunas             score +0.80  rating   1702  last5 3-2  ledger  6.0 (T10 9, T15 11 E)  days 246  band [2-3]
 5. Erin Blanchfield           score +0.75  rating   1721  last5 4-1  ledger  3.6 (T10 4, T15 5 E)  days 316  band [2-4]
 6. Maycee Barber              score +0.51  rating   1643  last5 4-1  ledger  3.3 (T10 4, T15 7 E)  days 183  band [6-6]
 7. Jasmine Jasudavicius       score +0.40  rating   1611  last5 4-1  ledger  2.8 (T10 3, T15 5 E)  days 162  band [7-8]
 8. Casey O'Neill              score +0.35  rating   1634  last5 3-2  ledger  0.3 (T10 0, T15 3)  days   8  band [7-8]
 9. Wang Cong                  score +0.28  rating   1600  last5 4-1  ledger  1.0 (T10 1, T15 3)  days  78  band [9-9]
10. Carli Judice               score +0.22  rating   1609  last5 4-1  ledger -1.0 (T10 0, T15 0)  days  36  band [10-10]
11. Miranda Maverick           score +0.18  rating   1587  last5 4-1  ledger -0.3 (T10 0, T15 2)  days 470  band [11-11]
12. Dione Barbosa              score +0.10  rating   1583  last5 3-2  ledger -2.0 (T10 0, T15 0)  days  71  band [12-13]
13. Regina Tarin               score +0.07  rating   1532  last5 2-0  ledger  0.5 (T10 0, T15 1)  days  15  band [12-15]
14. Tracy Cortez               score +0.03  rating   1589  last5 2-3  ledger -0.5 (T10 1, T15 1)  days  78  band [14-14]
15. JJ Aldrich                 score -0.05  rating   1530  last5 3-2  ledger -2.0 (T10 0, T15 0)  days  15  band [17-19]
16. Jamey-Lyn Horth            score +0.01  rating   1567  last5 3-2  ledger -3.0 (T10 0, T15 0)  days 162  band [13-16]
17. Karine Silva               score -0.03  rating   1583  last5 2-3  ledger -1.5 (T10 0, T15 1)  days 162  band [16-17]
18. Lauren Murphy              score -0.05  rating   1544  last5 2-3  ledger  0.6 (T10 4, T15 4 E)  days 442  band [15-18]
19. Viviane Araujo             score -0.11  rating   1516  last5 2-3  ledger  1.0 (T10 4, T15 7 E)  days 456  band [18-22]
20. Veronica Hardy             score -0.11  rating   1490  last5 4-1  ledger -0.8 (T10 0, T15 0)  days 358  band [20-21]
21. Luana Carolina             score -0.11  rating   1494  last5 3-2  ledger -1.0 (T10 0, T15 0)  days 365  band [19-21]
22. Nicolle Caliari            score -0.14  rating   1500  last5 1-2  ledger -2.0 (T10 0, T15 0)  days 134  band [20-22]
23. Gabriella Fernandes        score -0.17  rating   1473  last5 3-2  ledger -1.0 (T10 0, T15 0)  days 183  band [23-24]
24. Ernesta Kareckaite         score -0.18  rating   1487  last5 1-2  ledger -2.0 (T10 0, T15 0)  days 211  band [23-26]
25. Jeisla Chaves              score -0.20  rating   1464  last5 1-1  ledger -1.0 (T10 0, T15 0)  days  36  band [24-25]
26. Anna Melisano              score -0.20  rating   1462  last5 0-1  ledger -1.0 (T10 0, T15 0)  days  71  band [25-26]
27. Tereza Bleda               score -0.21  rating   1460  last5 1-2  ledger -1.0 (T10 0, T15 0)  days 288  band [27-28]
28. Yuneisy Duben              score -0.23  rating   1468  last5 0-2  ledger -2.0 (T10 0, T15 0)  days 113  band [27-28]
29. Ivana Petrovic             score -0.28  rating   1451  last5 1-3  ledger -2.0 (T10 0, T15 0)  days 512  band [29-29]
30. Juliana Miller             score -0.30  rating   1482  last5 2-3  ledger -1.0 (T10 0, T15 0)  days  50  band [30-31]

## Women's Bantamweight
 C. Kayla Harrison             score +0.48  rating   1611  last5 3-0  ledger  5.0 (T10 3, T15 3)  days 477  band [0-0]
 1. Joselyne Edwards           score +0.35  rating   1620  last5 5-0  ledger  1.5 (T10 1, T15 3)  days 155  band [2-3]
 2. Ailin Perez                score +0.39  rating   1606  last5 5-0  ledger  3.5 (T10 3, T15 3)  days   1  band [2-3]
 3. Norma Dumont               score +0.43  rating   1612  last5 3-2  ledger  3.8 (T10 4, T15 5 E)  days   1  band [1-1]
 4. Ketlen Vieira              score +0.22  rating   1560  last5 3-2  ledger  4.0 (T10 6, T15 9 E)  days 134  band [7-10]
 5. Jacqueline Cavalcanti      score +0.31  rating   1605  last5 4-1  ledger  2.0 (T10 1, T15 2)  days 134  band [4-6]
 6. Yana Santos                score +0.29  rating   1585  last5 3-2  ledger  3.4 (T10 3, T15 6 E)  days 358  band [4-7]
 7. Luana Santos               score +0.29  rating   1620  last5 4-1  ledger  0.0 (T10 1, T15 1)  days  99  band [4-8]
 8. Julianna Pena              score +0.27  rating   1587  last5 3-2  ledger  2.8 (T10 5, T15 5 E)  days 477  band [6-8]
 9. Bia Mesquita               score +0.27  rating   1616  last5 3-0  ledger  0.0 (T10 0, T15 0)  days  99  band [5-9]
10. Macy Chiasson              score +0.20  rating   1621  last5 2-3  ledger  1.4 (T10 3, T15 4)  days 211  band [9-10]
11. Michelle Montague          score +0.02  rating   1545  last5 2-0  ledger  1.0 (T10 0, T15 2)  days 155  band [11-13]
12. Karol Rosa                 score +0.01  rating   1585  last5 2-3  ledger  0.4 (T10 1, T15 4)  days  99  band [11-12]
13. Melissa Gatto              score -0.02  rating   1594  last5 2-3  ledger -1.0 (T10 0, T15 0)  days 176  band [11-15]
14. Melissa Croden             score -0.05  rating   1552  last5 2-1  ledger -1.0 (T10 0, T15 0)  days 162  band [14-14]
15. Nina Milosevic             score -0.08  rating   1534  last5 1-0  ledger  0.0 (T10 0, T15 0)  days  57  band [14-15]
16. Alice Pereira              score -0.14  rating   1529  last5 1-1  ledger -1.0 (T10 0, T15 0)  days 176  band [16-16]
17. Nora Cornolle              score -0.22  rating   1562  last5 2-3  ledger -2.5 (T10 0, T15 1)  days  22  band [17-18]
18. Miesha Tate                score -0.27  rating   1521  last5 2-3  ledger  0.2 (T10 4, T15 6 E)  days 512  band [17-18]
19. Klaudia Sygula             score -0.34  rating   1494  last5 2-2  ledger -2.0 (T10 0, T15 0)  days  22  band [19-19]
20. Daria Zhelezniakova        score -0.36  rating   1489  last5 2-2  ledger -2.0 (T10 0, T15 0)  days 162  band [20-20]
21. Montse Rendon              score -0.44  rating   1470  last5 2-2  ledger -2.0 (T10 0, T15 0)  days 197  band [21-21]
22. Chelsea Chandler           score -0.48  rating   1491  last5 2-3  ledger -1.5 (T10 0, T15 1)  days 113  band [22-22]
23. Tainara Lisboa             score -0.50  rating   1455  last5 2-2  ledger -2.0 (T10 0, T15 0)  days 344  band [23-23]
24. Irina Alekseeva            score -0.64  rating   1434  last5 1-3  ledger -3.0 (T10 0, T15 0)  days 351  band [24-24]
25. Melissa Mullins            score -0.70  rating   1456  last5 2-3  ledger -3.0 (T10 0, T15 0)  days  99  band [25-25]
26. Hailey Cowan               score -0.86  rating   1382  last5 0-4  ledger -3.0 (T10 0, T15 0)  days  57  band [26-26]
27. Mayra Bueno Silva          score -1.25  rating   1494  last5 0-5  ledger -4.4 (T10 0, T15 1)  days 155  band [27-27]
28. Priscila Cachoeira         score -1.35  rating   1419  last5 1-4  ledger -4.0 (T10 0, T15 0)  days 113  band [28-28]

## Head-to-head moves applied
- Bantamweight: Raoni Barcelos moved above Payton Talbott (won 2025-01-18)
- Bantamweight: Sean O'Malley moved above Song Yadong (won 2026-01-24)
- Bantamweight: Raoni Barcelos moved above Montel Jackson (won 2026-04-25)
- Bantamweight: Raul Rosas Jr. moved above Raoni Barcelos (won 2026-09-26)
- Featherweight: Pat Sabatini moved above Joanderson Brito (won 2025-04-05)
- Featherweight: Dooho Choi moved above Daniel Santos (won 2026-05-16)
- Featherweight: Pavel Andrusca moved above Nathaniel Wood (won 2026-09-05)
- Heavyweight: Denzel Freeman moved above Marek Bujlo (won 2025-11-22)
- Heavyweight: Tyrell Fortune moved above Marcin Tybura (won 2026-03-28)
- Heavyweight: Josh Hokit moved above Curtis Blaydes (won 2026-04-11)
- Light Heavyweight: Modestas Bukauskas moved above Christian Edwards (won 2026-05-16)
- Light Heavyweight: Alonzo Menifield moved above Iwo Baraniewski (won 2026-09-19)
- Lightweight: King Green moved above Grant Dawson (won 2023-10-07)
- Lightweight: Renato Moicano moved above Benoit Saint Denis (won 2024-09-28)
- Lightweight: Ilia Topuria moved above Charles Oliveira (won 2025-06-28)
- Lightweight: Mauricio Ruffy moved above Rafael Fiziev (won 2026-01-31)
- Lightweight: Charles Oliveira moved above Max Holloway (won 2026-03-07)
- Lightweight: Kody Steele moved above Dom Mar Fan (won 2026-05-02)
- Middleweight: Marco Tulio moved above Tresean Gore (won 2025-04-12)
- Middleweight: Khamzat Chimaev moved above Dricus Du Plessis (won 2025-08-16)
- Welterweight: Ian Machado Garry moved above Carlos Prates (won 2025-04-26)
- Welterweight: Jack Della Maddalena moved above Belal Muhammad (won 2025-05-10)
- Welterweight: Ramiz Brahimaj moved above Austin Vanderford (won 2025-10-04)
- Welterweight: Michael Morales moved above Sean Brady (won 2025-11-15)
- Welterweight: Yaroslav Amosov moved above Neil Magny (won 2025-12-13)
- Welterweight: Gabriel Bonfim moved above Belal Muhammad (won 2026-06-06)
- Welterweight: Jean-Paul Lebosnoyani moved above Seokhyeon Ko (won 2026-07-18)
- Welterweight: Uros Medic moved above Daniel Rodriguez (won 2026-08-01)
- Women's Bantamweight: Joselyne Edwards moved above Norma Dumont (won 2026-04-25)
- Women's Bantamweight: Ketlen Vieira moved above Jacqueline Cavalcanti (won 2026-05-16)
- Women's Bantamweight: Ailin Perez moved above Norma Dumont (won 2026-09-26)
- Women's Flyweight: Natalia Silva moved above Rose Namajunas (won 2026-01-24)
- Women's Flyweight: JJ Aldrich moved above Jamey-Lyn Horth (won 2026-04-18)
- Women's Flyweight: Alexa Grasso moved above Manon Fiorot (won 2026-09-12)
- Women's Strawweight: Ketlen Souza moved above Yazmin Jauregui (won 2024-09-14)
- Flyweight: Alexandre Pantoja #1 -> #4 (lost a title fight 2026-09-19; the champion fights someone else next)
- Flyweight: Tatsuro Taira #3 -> #5 (lost a title fight 2026-05-09; the champion fights someone else next)
- Flyweight: Brandon Moreno #4 -> #6 (lost to a fighter moved by the title-cycle rule in the last year)
- Heavyweight: Alex Pereira #1 -> #4 (lost a title fight 2026-06-14; the champion fights someone else next)
- Light Heavyweight: Jiri Prochazka #2 -> #4 (lost a title fight 2026-04-11; the champion fights someone else next)
- Welterweight: Ian Machado Garry #3 -> #4 (lost a title fight 2026-08-15; the champion fights someone else next)

## 8. Benchmark review against published rating systems

# Benchmark review: REAL Fighter Rankings against published rating systems

Compiled Oct 1, 2026 from the sources listed at the end. This is the internal review that fed METHODOLOGY.md section 10.

## Comparable methods

1. Fight Matrix (MMA). Publishes four systems side by side: Standard Elo (K=170, start 1000), Modified Elo (K varies with experience, +15 home bonus), Glicko-1, and Whole-History Rating. Split and majority decisions count as partial results (0.667/0.333 and 0.833/0.167). Inactive fighters lose rating progressively and can win most of it back in their first two comeback fights; in the Glicko version, rating deviation rises with inactivity to a cap of 230. Opponent strength uses a "540 Opponent Metric" over a 1,080-day window. Updated weekly. No accuracy figures published.
2. BoxRec (boxing). Whole-History Rating, a Bradley-Terry model refit over every fighter's full history. Each result is a fraction: stoppage 1.0; without scorecards UD 0.875, MD 0.55, SD 0.45; with scorecards, the average judge margin per round. Decisions in bouts shorter than 12 rounds are down-weighted by (rounds/12)^2. New boxers start from seeded prior bouts; inactivity adds weak prior bouts each year, pulling the rating toward the base. Rule: for 36 months a winner stays ranked above the loser.
3. FIFA World Ranking (SUM, since 2018). P = P_before + I(W - W_e), W_e = 1/(10^(-dr/600)+1). Importance I from 5 to 60 by match type. A knockout-stage loss at a final tournament costs nothing. Shootout: 0.75 winner, 0.5 loser. No margin of victory, no decay.
4. World Rugby. Points exchange (gain = opponent's loss), 3-point home handicap, 1.5x for wins by more than 15 points, World Cup exchanges doubled, movement per match capped. No decay.
5. FiveThirtyEight NFL Elo (public code). K=20, home field 65. Margin multiplier = ln(margin+1) x 2.2/(winner Elo difference x 0.001 + 2.2), the second term being the autocorrelation fix so favorites are not over-rewarded for routs. Between seasons ratings regress one third toward 1505.
6. Glicko/Glicko-2 (Glickman) and TrueSkill (Microsoft, 2006). Each rating carries a deviation (uncertainty) that grows with inactivity; Glicko-2 adds volatility. TrueSkill models skill as a normal distribution and ranks on the conservative mu - 3 sigma.
7. Tennis Elo (Sackmann). Overall and surface ratings blended 50/50; after a long absence the rating drops and post-return matches are weighted more; validated against ATP/WTA rankings with the Brier score.
8. Colley, Massey, NCAA NET. Colley uses wins and losses only (no margin, to remove the incentive to run up scores); Massey fits point margins; Devlin and Treloar (JQAS 2018) unify Markov, Massey and Colley and test with 10-fold cross-validation over 33 seasons. The NCAA separates results-based metrics (NET, Strength of Record) from predictive ones (KenPom, BPI).
9. Holmes, McHale and Zychaluk (International Journal of Forecasting, 2023). Markov-chain simulation of UFC fights trained 2001-2017, tested on 2018: 61.8% accuracy vs 61.2% for bookmakers; a Bradley-Terry benchmark scored 54.1%.
10. CMU statistics capstone (2025). Crossed random-effects logistic model, trained 2016-2022, tested 2023-24: 68.4% against a 66.7% market-favorite baseline.

## Comparison table

| Method | Margin of victory | Opponent strength | Recency / decay | Inactivity | Uncertainty | Validation | Published |
|---|---|---|---|---|---|---|---|
| REAL v1.0 | Cards 50% + stats 50% | Elo + official rank tiers | Ledger weights 1/0.6/0.3/0.1; last-five penalty | Grace, injury exemption | Weight-perturbation bands | Predictive Elo 61.2% vs market 65.2%; resume board 3-year rebuild 54.4% | Site, METHODOLOGY.md, audit trail |
| Fight Matrix | Decision type | Elo + 540 metric | Recent weighted | Progressive decline | Glicko RD | None published | FAQ, weekly |
| BoxRec | Judge margin per round | WHR full refit | Implicit | Prior pulls to base | None shown | None published | Wiki formula |
| FIFA SUM | None | Expected result | None | None | None | None | Full PDF |
| World Rugby | 1.5x if >15 | Rating gap | None | None | None | None | Explainer |
| FiveThirtyEight Elo | Log margin + autocorrelation fix | Elo | Season regression | Season regression | None | Calibration | Code + method |
| Glicko / TrueSkill | None | Bayesian | Dynamics term | Deviation grows | Core feature | Academic | Papers |
| Tennis Elo | None | Elo | Variable K | Post-return reweight | None | Brier vs ATP | Blog |
| Colley / NET | None / efficiency | Linear system / quadrants | None | n/a | None | Cross-validation | Paper / NCAA |
| Holmes et al. | Simulated stats | Bayesian GLMs | Train/test split | n/a | Probabilistic | Out-of-sample vs bookmakers | Journal |

## Best practices and REAL's status

| Practice | Status | Why |
|---|---|---|
| Separate resume ranking from prediction | Met | Two systems, two pages |
| Validate forward in time, out of sample | Met for prediction; started for resume board | Resume rebuild is in-sample until the v1.0 freeze |
| Score probabilities (log loss, Brier, calibration), not just picks | Met for prediction | Resume board reports only pick accuracy |
| Compare to market and naive baselines on the same fights | Partly met | Market yes; a "favorite wins" baseline not reported |
| Per-fighter uncertainty (RD, sigma) | Partly met | Stability bands show weight sensitivity, not sample size |
| Correct margin-of-victory autocorrelation | Not met | Dominance inputs have no favorite-adjusted damping |
| Bounded, documented asymmetric protections | Partly met | Specified, but pool-level inflation not checked |
| Minimum-sample or provisional rules | Not met | One UFC bout makes a fighter eligible |
| Inactivity through uncertainty rather than exemptions | Partly met | Injury exemptions are hand-kept |
| Log every rule-based placement | Met | audit_top30.csv records score order and each rule move |
| Versioned methodology and changelog | Met from v1.0 | METHODOLOGY.md generated from config; VERSION file |
| Constants fit on held-out data | Partly met | Prediction model grid-searched; resume constants set by stated principle |

## Five highest-value changes for v1.1

1. Per-fighter uncertainty (Glicko-style deviation), provisional status under a minimum fight count, intervals added to the stability bands.
2. Forward validation of the resume board on post-freeze bouts with log loss and Brier, against a "favorite wins" baseline and the official board on identical bouts.
3. Damp the dominance term for favorites (FiveThirtyEight factor) and check that cards plus stats do not double count the same dominance.
4. Fit the hand-set constants (loss protection 15%/75%, ledger weights, 50/50 blend) on held-out log loss, or refit with a whole-history model as a retrospective check.
5. Keep the version number, changelog and placement log public with each weekly release.

## Sources
- https://www.fightmatrix.com/faq/
- https://www.fightmatrix.com/2020/06/23/whr-and-how-it-really-differs-from-elo-glicko/
- https://boxrec.com/wiki/index.php/BoxRec_Ratings_Description
- https://inside.fifa.com/fifa-world-ranking/procedure-men
- https://www.world.rugby/rankings/explanation
- https://github.com/fivethirtyeight/nfl-elo-game
- https://en.wikipedia.org/wiki/Glicko_rating_system
- https://en.wikipedia.org/wiki/TrueSkill
- https://www.tennisabstract.com/blog/2019/12/03/an-introduction-to-tennis-elo/
- https://www.colleyrankings.com/matrate.pdf
- https://www.degruyterbrill.com/document/doi/10.1515/jqas-2017-0098/html
- https://www.ncaa.org/media-center-how-do-net-rankings-work-in-ncaa-tournament-selection/
- https://www.sciencedirect.com/science/article/pii/S0169207022000073
- https://www.stat.cmu.edu/capstoneresearch/460files_s25/team11.pdf


## 9. Known limitations and open items (author's own list)

1. Resume-board constants (loss protection 15%/75%, ledger tier values, age weights, form penalties, head-to-head and title-cycle windows) were set by stated principle and checked for sensitivity; they were not fit to data. The predictive model's parameters were grid-searched on 2010-2019 and tested once on 2020-2026.
2. The resume board's forward check uses boards rebuilt with today's rules, so it is in-sample; true forward grading starts with bouts after Oct 1, 2026.
3. No pre-UFC records: debutants start at the same rating. No betting odds after Dec 2023, so 'heavy favorite' uses the model's own probability. Both are planned for v1.1 from public datasets.
4. Hand-kept configuration (retirements, injuries, vacated titles, division moves, short-notice bouts) is reviewed weekly by a scheduled process that proposes changes for the author's approval; each entry carries its source.
5. Official UFC rankings history matched about 99% of ranked names to UFCStats names; 13 historical names were unmatched and treated as unranked.
6. Judges' scorecards cover 98.6% of decisions (100% since 2005). Strike counts are hand-coded by the official provider and do not measure damage.
7. 25 duplicate bouts (two Noche UFC cards listed under two names by the scraper) were found and removed on Sept 30, 2026; all numbers in this package postdate that fix.
8. Legal: 'REAL Fighter Rankings' is a new name chosen Sept 30, 2026 after a trademark and right-of-publicity review of the earlier working name; the site carries a non-affiliation disclaimer and uses no UFC marks, logos or fighter likenesses.

## 10. Data sources and licenses

- UFCStats.com (official UFC statistics provider), via Greco1899/scrape_ufc_stats (GitHub), refreshed after every event. Fields: results, method, round, time, judges' cards, round-by-round strikes, knockdowns, takedowns, submission attempts, control time.
- martj42/ufc_rankings_history (GitHub): every official media-panel ranking release Feb 4, 2013 to June 16, 2026 (Kaggle twin is CC0). Extended with snapshots of ufc.com/rankings.
- jansen88/ufc-data (GitHub): closing odds Nov 2014 to Dec 2023 (3,499 bouts matched), originally from betmma.tips.
- Public boards for comparison: ufc.com/rankings (media panel and Meta), sherdog.com, fightmatrix.com, espn.com.
- The UFC's own announcements used for context: Meta UFC Rankings transition (June 22, 2026); IBM Insights Engine partnership (Nov 2024); Paramount+ schedule of 13 numbered events and 30 Fight Nights per year (2026).