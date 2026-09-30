| Model | Log loss, tune 2010-19 | Log loss, test 2020-26 | Brier, test | Accuracy, test |
|---|---|---|---|---|
| Coin flip | - | 0.6931 | - | 50.0% |
| Classic Elo, untuned (K=32) | 0.6849 | 0.6833 | 0.2451 | 56.7% |
| Classic Elo, tuned (results only) | 0.6801 | 0.673 | 0.2401 | 58.2% |
| Performance-adjusted Elo, tuned | 0.6639 | 0.6618 | 0.2346 | 60.6% |
| Performance-adjusted Elo, interpretable (win/finish floors) | 0.6675 | 0.6607 | 0.2341 | 61.3% |

Test bouts: 3,412. Tuning bouts: 4,116.

Same-bout comparison against the closing betting market (de-vigged), 3,507 bouts, 2014-11-07 to 2023-12-16:

| Model | Log loss | Brier | Accuracy |
|---|---|---|---|
| Performance-adjusted Elo | 0.6678 | 0.2373 | 59.7% |
| Betting market | 0.6156 | 0.2138 | 65.2% |
| 50/50 blend | 0.6315 | 0.2203 | 64.9% |