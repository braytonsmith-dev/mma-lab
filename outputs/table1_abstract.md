Table 1. Held-out prediction, 2020-2026. Parameters fixed by a 520-point grid on 2010-2019 (4,116 bouts); the selected specification was scored once on the held-out bouts.

| Model | Bouts | Log loss | Change vs results-only (95% event-block bootstrap CI) | Brier | Accuracy | McNemar p |
|---|---|---|---|---|---|---|
| Results-only Elo | 3,390 | 0.674 | | 0.241 | 58.1% | |
| Performance-adjusted Elo | 3,390 | 0.663 | -0.011 (-0.016 to -0.006) | 0.235 | 60.6% | 0.002 |
| Results-only Elo | 1,445* | 0.675 | | 0.241 | 57.8% | |
| Performance-adjusted Elo | 1,445* | 0.669 | | 0.238 | 60.0% | |
| Closing betting market, de-vigged | 1,445* | 0.609 | | 0.210 | 67.1% | |

*Held-out bouts with closing odds, 2020-01-18 to 2023-12-16. Log loss: coin flip 0.693; lower is better. Accuracy: share of bouts in which the fighter given more than 50% won. McNemar: exact test on the 773 bouts the two models call differently (429 fixed, 344 broken).