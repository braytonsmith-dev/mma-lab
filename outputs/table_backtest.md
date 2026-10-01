Table 1. Held-out prediction, 2020-2026. Parameters fixed by a 520-point grid on 2010-2019 (4,116 bouts); the selected specification was scored once on the held-out bouts.

| Model | Bouts | Log loss | Change vs results-only (95% event-block bootstrap CI) | Brier | Accuracy | McNemar p |
|---|---|---|---|---|---|---|
| Results-only Elo | 3,390 | 0.674 | | 0.241 | 58.1% | |
| Performance-adjusted Elo | 3,390 | 0.663 | -0.011 (-0.016 to -0.006) | 0.235 | 60.6% | 0.002 |
| Results-only Elo | 1,445* | 0.675 | | 0.241 | 57.8% | |
| Performance-adjusted Elo | 1,445* | 0.669 | | 0.238 | 60.0% | |
| Closing betting market, de-vigged | 1,445* | 0.609 | | 0.210 | 67.1% | |

*Held-out bouts with closing odds, 2020-01-18 to 2023-12-16. Log loss: coin flip 0.693; lower is better. Accuracy: share of bouts in which the fighter given more than 50% won. McNemar: exact test on the 773 bouts the two models call differently (429 fixed, 344 broken).

Full comparison (the interpretable site specification is a second model scored on the same window and is not the pre-registered result):

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