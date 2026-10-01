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
