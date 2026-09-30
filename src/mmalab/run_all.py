"""
run_all.py - One command to rebuild everything from the raw CSVs.

    PYTHONPATH=src python3 -m mmalab.run_all            # full rebuild (~4 min)
    PYTHONPATH=src python3 -m mmalab.run_all --quick    # skip the Elo grid search (~2 min)

Order matters: ingest -> bout_stats -> backtest -> rankings -> card_quality -> figures -> publish
"""
from __future__ import annotations

import sys
import time

from pathlib import Path

import yaml

from mmalab import ingest, bout_stats, backtest, rankings, resume_board, card_quality, figures, publish, compare


def main(quick: bool = False) -> None:
    steps = [("ingest", ingest.main), ("bout_stats", bout_stats.main)]
    if not quick:
        steps.append(("backtest", backtest.main))
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / "config" / "weights.yaml").read_text())
    board = resume_board.main if cfg.get("board_model") == "resume" else rankings.main
    steps += [("boards", board), ("card_quality", card_quality.main), ("compare", compare.main),
              ("figures", figures.main), ("publish", publish.main)]
    for name, fn in steps:
        t = time.time()
        print(f"\n===== {name} =====")
        fn()
        print(f"----- {name} done in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
