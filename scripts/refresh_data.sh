#!/usr/bin/env bash
# Pull the latest UFCStats CSVs (refreshed after every event by Greco1899/scrape_ufc_stats)
# and the historical odds file, then rebuild every output.
#
#   bash scripts/refresh_data.sh            # full rebuild including the Elo grid search (~4 min)
#   bash scripts/refresh_data.sh --quick    # skip the grid search (~2 min)
set -euo pipefail
cd "$(dirname "$0")/.."

BASE=https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main
for f in ufc_event_details ufc_fight_results ufc_fight_details ufc_fight_stats ufc_fighter_details ufc_fighter_tott; do
  curl -sSL "$BASE/$f.csv" -o "data/raw/$f.csv"
done
# official rankings history (martj42), appended weekly upstream when maintained
curl -sSL https://raw.githubusercontent.com/martj42/ufc_rankings_history/master/rankings_history.csv \
  -o data/raw/ufc_rankings_history.csv || true
# odds file only changes if you re-scrape; keep the committed copy unless a newer one is provided
if [ ! -f data/raw/odds_bestfightodds_2014_2023.csv ]; then
  curl -sSL https://raw.githubusercontent.com/jansen88/ufc-data/main/data/cleaned_odds.csv \
    -o data/raw/odds_bestfightodds_2014_2023.csv
fi

PYTHONPATH=src python3 -m mmalab.run_all "$@"
echo "Rebuilt. Boards: outputs/composite_boards.md"
