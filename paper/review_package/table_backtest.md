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