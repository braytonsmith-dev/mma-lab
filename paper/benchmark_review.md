# Benchmark review: REAL Fighter Rankings against published rating systems

Compiled Sept 30, 2026 from the sources listed at the end and corrected Oct 1, 2026 after an independent hostile review (corrections marked). This is the internal review that fed METHODOLOGY.md section 10.

## Comparable methods

1. Fight Matrix (MMA). Publishes four systems side by side: Standard Elo (K=170, start 1000), Modified Elo (K varies with experience, +15 home bonus), Glicko-1, and Whole-History Rating. Split and majority decisions count as partial results (0.667/0.333 and 0.833/0.167). Inactive fighters lose rating progressively and can win most of it back in their first two comeback fights; in the Glicko version, rating deviation rises with inactivity to a cap of 230. Opponent strength uses a "540 Opponent Metric" over a 1,080-day window. Updated weekly. No accuracy figures published.
2. BoxRec (boxing). Whole-History Rating, a Bradley-Terry model refit over every fighter's full history. Each result carries a clear-decision factor cd (stoppage 1.0; without scorecards UD 0.875, MD 0.55, SD 0.45; with scorecards, derived from the judges' margins) and the bout result entered in the model is (1 + cd) / 2, so an unscored unanimous decision enters as 0.9375, not 0.875 (corrected Oct 1). Decisions in bouts shorter than 12 rounds are down-weighted by (rounds/12)^2. New boxers start from seeded prior bouts; inactivity adds weak prior bouts each year, pulling the rating toward the base. Rule: for 36 months a winner stays ranked above the loser.
3. FIFA World Ranking (SUM, since 2018). P = P_before + I(W - W_e), W_e = 1/(10^(-dr/600)+1). Importance I from 5 to 60 by match type. A knockout-stage loss at a final tournament costs nothing. Shootout: 0.75 winner, 0.5 loser. No margin of victory, no decay.
4. World Rugby. Points exchange (gain = opponent's loss), 1.5x for wins by more than 15 points, World Cup exchanges doubled, movement per match capped. No decay. The 3-point home handicap was removed with effect from July 1, 2026 (corrected Oct 1; the earlier draft cited the superseded rule).
5. FiveThirtyEight NFL Elo (public code). K=20, home field 65. Margin multiplier = ln(margin+1) x 2.2/(winner Elo difference x 0.001 + 2.2), the second term being the autocorrelation fix so favorites are not over-rewarded for routs. Between seasons ratings regress one third toward 1505.
6. Glicko/Glicko-2 (Glickman) and TrueSkill (Microsoft, 2006). Each rating carries a deviation (uncertainty) that grows with inactivity; Glicko-2 adds volatility. TrueSkill models skill as a normal distribution and ranks on the conservative mu - 3 sigma.
7. Tennis Elo (Sackmann). Overall and surface ratings blended 50/50; after a long absence the rating drops and post-return matches are weighted more; validated against ATP/WTA rankings with the Brier score.
8. Colley, Massey, NCAA NET. Colley uses wins and losses only (no margin, to remove the incentive to run up scores) and describes its target as deservedness rather than prediction; Massey fits point margins; Devlin and Treloar (JQAS 2018) unify Markov, Massey and Colley and test with 10-fold cross-validation over 33 seasons. NCAA selection practice separates results-based metrics (WAB, KPI, Strength of Record) from predictive ones (Torvik, BPI, KenPom); the NET itself blends both, so the honest comparator is the selection practice, not the NET (corrected Oct 1).
9. Holmes, McHale and Zychaluk, A Markov chain model for forecasting results of mixed martial arts contests, International Journal of Forecasting 39(2), 623-640 (2023). Markov-chain simulation of UFC fights with an out-of-sample comparison against bookmakers. The 61.8% vs 61.2% accuracy figures and the 54.1% Bradley-Terry benchmark are quoted from memory of the paper and could not be re-verified from the publicly accessible page on Oct 1, 2026; they must be checked against the article PDF before the full paper cites them (flagged by the hostile review). Raw accuracy across different eras and samples is not directly comparable in any case.
10. CMU statistics capstone (2025). Crossed random-effects logistic model, trained 2016-2022, tested 2023-24: 68.4% against a 66.7% market-favorite baseline. A student capstone, not peer reviewed; the exact percentages could not be re-verified from the showcase page on Oct 1, 2026 and need a stable PDF citation before the full paper uses them. A market-favorite classification baseline is also not the same test as de-vigged closing probabilities scored by log loss.

## Comparison table

| Method | Margin of victory | Opponent strength | Recency / decay | Inactivity | Uncertainty | Validation | Published |
|---|---|---|---|---|---|---|---|
| REAL v1.0 | Cards 50% + stats 50% | Elo + official rank tiers | Ledger weights 1/0.6/0.3/0.1; last-five penalty | Grace, injury exemption | Weight-sensitivity band only (not skill uncertainty) | Predictive Elo 60.6% and 0.663 log loss on 3,390 held-out bouts (paired gain over results-only Elo 0.011, 95% CI 0.006 to 0.016); market 67.1% and 0.609 on the 1,445 held-out bouts with odds; resume board retrospective reconstruction 54.4% (95% CI 48% to 61%) | Site, METHODOLOGY.md, audit trail, PREREGISTRATION.md |
| Fight Matrix | Decision type | Elo + 540 metric, over full professional MMA records (no UFC-debut cold start) | Recent weighted | Progressive decline; Glicko RD rises after 180 days | Glicko RD, start and cap 230 | None published | FAQ, weekly |
| BoxRec | Judge margin per round | WHR full refit | Implicit | Prior pulls to base | None shown | None published | Wiki formula |
| FIFA SUM | None | Expected result | None | None | None | None | Full PDF |
| World Rugby | 1.5x if >15 | Rating gap (home handicap removed July 2026) | None | None | None | None | Explainer |
| FiveThirtyEight Elo | Log margin + autocorrelation fix | Elo | Season regression | Season regression | None | Calibration | Code + method |
| Glicko / TrueSkill | None | Bayesian | Dynamics term | Deviation grows | Core feature | Academic | Papers |
| Tennis Elo | None | Elo | Variable K | Post-return reweight | None | Brier vs ATP | Blog |
| Colley / NET | None / efficiency | Linear system / quadrants | None | n/a | None | Cross-validation | Paper / NCAA |
| Holmes et al. | Simulated stats | Bayesian GLMs | Train/test split | n/a | Probabilistic | Out-of-sample vs bookmakers | Journal |

## Best practices and REAL's status

| Practice | Status | Why |
|---|---|---|
| Separate resume ranking from prediction | Met | Two systems, two pages |
| Validate forward in time, out of sample | Met for prediction; not yet for the resume board | The 127-board rebuild is a retrospective reconstruction with today's rules (54.4%, 95% Wilson interval 48% to 61%, exact binomial p = 0.21 against 50%); the prospective test starts Oct 2, 2026 under PREREGISTRATION.md |
| Score probabilities (log loss, Brier, calibration), not just picks | Met for prediction | Resume board reports only pick accuracy |
| Compare to market and naive baselines on the same fights | Met for prediction | Market, results-only Elo and the model are scored on exactly the 1,445 held-out bouts with odds; paired bootstrap and McNemar reported |
| Per-fighter uncertainty (RD, sigma) | Not met | The weight band is a sensitivity interval for the 70/30 weights, recomputed after every placement rule so the published rank lies inside it; it says nothing about sparse records or inactivity |
| Correct margin-of-victory autocorrelation | Not met | Dominance inputs have no favorite-adjusted damping; the dominance sign agrees with the winner in about 86% of bouts, so a high dominance weight may partly be a high-resolution proxy for the result |
| Bounded, documented asymmetric protections | Partly met | Specified, but pool-level inflation not checked |
| Minimum-sample or provisional rules | Not met | One UFC bout makes a fighter eligible |
| Inactivity through uncertainty rather than exemptions | Partly met | Injury exemptions are hand-kept |
| Log every rule-based placement | Met | audit_top30.csv records score order and each rule move |
| Versioned methodology and changelog | Met from v1.0 | METHODOLOGY.md generated from config; VERSION file |
| Constants fit on held-out data | Partly met | Prediction model selected on a disclosed 520-point grid; resume constants set by stated principle and checked against public boards, which makes those boards an informal tuning target |

## Items the hostile review added (Oct 1, 2026)

- The resume rating can rise after a loss (proof-of-concept credit) and the same loss can also enter the ledger and the form penalty; v1.1 gives each channel one role.
- Top-3 and title-fight loss protection duplicates what the Elo expected score already does for underdogs.
- The official-rank tiers import the media panel's judgments into a system presented as independent.
- The last-five penalty is a discrete, high-leverage second rating; interdecile scaling makes its effective weight depend on each division's current spread.
- Head-to-head and title-cycle swaps are order-dependent procedures rather than a solved constrained ordering.
- Hand-kept overrides need effective dates and source evidence; the 13 unmatched historical ranking names become "unranked", a directional error.
- The red-corner (first-listed) fighter wins 57.2% of held-out bouts against 53.5% predicted: the model carries no corner term.

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
