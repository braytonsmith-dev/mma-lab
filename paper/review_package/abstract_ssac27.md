# Performance-Adjusted Elo for Mixed Martial Arts: In-Fight Statistics Improve UFC Rankings and Measure the Card-Quality Gap

Track: Other Sports. Author: Brayton Smith, PhD, MBA. Repository: https://github.com/braytonsmith-dev/mma-lab

## Introduction

In June 2026 the UFC began replacing its media-voted rankings with an Elo-style model built with Meta that uses results, opponent quality, and recency. Two questions decide whether a data-driven ranking deserves trust: does it predict outcomes, and what does it reveal about matchmaking? We build an open, reproducible rating system from public UFCStats data, test whether round-level statistics improve on results-only Elo, and measure how ranked-versus-ranked bouts are distributed across the promotion's 43-event calendar.

## Methods

Data: 8,911 UFC bouts from March 1994 to September 2026 with round-level statistics for 99.8%. Classic Elo updates on the binary result. Performance-adjusted Elo replaces the result with a blend of the result and a logistic transform of a per-minute dominance differential (significant strikes, knockdowns weighted 5, takedowns 2, submission attempts 2, control time), with a floor so a win never scores below 0.5. Both variants use a larger K for a fighter's first five UFC bouts and regression toward the mean after layoffs longer than a year. All parameters were chosen by grid search on 2010-2019 bouts (log loss) and evaluated once on 3,390 held-out 2020-2026 bouts. Ratings were also compared with de-vigged closing odds on 3,499 matched bouts (2014-2023). For every event since 2022, each fighter was positioned within their division among fighters active in the prior 18 months by pre-fight rating, and a bout was tagged "top 10" when both fighters sat inside positions 1-11 (champion plus ten).

## Results

Table 1 summarizes prediction. Performance adjustment lowers held-out log loss from 0.674 to 0.662 and raises accuracy from 58.1% to 61.2%; a 90% weight on dominance is optimal, and finish multipliers add nothing once dominance is included. The betting market remains stronger (0.616, 65.2%), so the model is a ranking instrument rather than a betting edge. Figure 1 shows the card-quality index: 203 cards from 2022 through September 2026 average 1.2 top-10 bouts each, numbered events 2.2 and Fight Nights 0.7, and 31% to 54% of Fight Nights carry none. Supply binds before scheduling does: fighters who begin a year inside a top 11 average 1.3 to 1.4 bouts that year, 12% to 16% do not compete at all (2022-2025), and 58% to 62% of their bouts are already against another top-11 opponent, which caps the achievable number of ranked bouts near 50 per year.

## Conclusion

Round-level statistics carry ranking information that results alone miss. We pair the predictive model with REAL Fighter Rankings, a weekly resume board that values each win by the opponent's official rank at fight time, blends judges' cards with fight statistics, and publishes an audit trail for every placement. The card-quality index confirms the "stacked card" complaint but bounds the remedy: with roughly 50 ranked-versus-ranked bouts available per year, redistribution across 43 cards, not more matchups, is the actionable lever. Code, data, and weekly boards are open source at the repository above.

---

Word count target: under 500 including title (see paper/abstract_wordcount.txt after running `wc -w`).

Table 1 (paste from outputs/table_backtest.md). Figure 1: outputs/fig_card_quality.png.
