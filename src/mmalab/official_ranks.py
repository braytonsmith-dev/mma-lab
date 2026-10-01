"""
official_ranks.py - Official UFC media-panel rank of each fighter on any date (Feb 2013 on).

Source: martj42/ufc_rankings_history (every release 2013-02-04 to 2026-06-16), extended
with any later snapshots saved in data/external/ufc_media.csv. Rank 0 = champion.
Before Feb 2013, or for a division with no release yet, callers fall back to the
model's own position.
"""
from __future__ import annotations

import bisect
import difflib
from pathlib import Path

import pandas as pd

from mmalab.compare import norm

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
EXT = ROOT / "data" / "external"

DIVS = {"Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight",
        "Light Heavyweight", "Heavyweight", "Women's Strawweight", "Women's Flyweight",
        "Women's Bantamweight", "Women's Featherweight"}


class OfficialRanks:
    def __init__(self, ufc_names: list[str]):
        r = pd.read_csv(RAW / "ufc_rankings_history.csv")
        r = r[r["weightclass"].isin(DIVS)].copy()
        r["date"] = pd.to_datetime(r["date"])
        if (EXT / "ufc_media.csv").exists():
            m = pd.read_csv(EXT / "ufc_media.csv")
            m = pd.DataFrame({"date": pd.to_datetime(m["as_of"]), "weightclass": m["division"],
                              "fighter": m["fighter"], "rank": m["rank"]})
            r = pd.concat([r, m[m["date"] > r["date"].max()]], ignore_index=True)
        # map ranking names onto UFCStats names
        known = {norm(n): n for n in ufc_names}
        keys = list(known)
        mapping, self.unmatched = {}, set()
        for name in r["fighter"].unique():
            k = norm(name)
            if k in known:
                mapping[name] = known[k]
                continue
            c = difflib.get_close_matches(k, keys, n=1, cutoff=0.88)
            if c and len(c[0].split()) == len(k.split()) and all(
                    difflib.SequenceMatcher(None, x, y).ratio() >= 0.85 for x, y in zip(k.split(), c[0].split())):
                mapping[name] = known[c[0]]
            else:
                self.unmatched.add(name)
        r["ufc_name"] = r["fighter"].map(mapping)
        r = r.dropna(subset=["ufc_name"])
        self.dates = sorted(r["date"].unique())
        self.first, self.last = self.dates[0], self.dates[-1]
        self.by_date: dict = {}
        for d, g in r.groupby("date"):
            self.by_date[d] = {
                "div": {(w, n): int(k) for w, n, k in zip(g["weightclass"], g["ufc_name"], g["rank"])},
                "any": g.groupby("ufc_name")["rank"].min().astype(int).to_dict(),
                "divs": set(g["weightclass"]),
            }
        self.match_rate = 1 - len(self.unmatched) / max(r["fighter"].nunique() + len(self.unmatched), 1)

    def release_before(self, date) -> pd.Timestamp | None:
        i = bisect.bisect_left(self.dates, pd.Timestamp(date)) - 1
        return self.dates[i] if i >= 0 else None

    def rank(self, name: str, division: str, date) -> float | None:
        """Official rank going into a bout on `date`: 0 champion, 1-15, 99 unranked; None if no
        official board existed yet (pre-2013 or a division not yet ranked)."""
        d = self.release_before(date)
        if d is None:
            return None
        rel = self.by_date[d]
        if division in DIVS and division not in rel["divs"]:
            return None                          # division not ranked on that date
        if (division, name) in rel["div"]:
            return float(rel["div"][(division, name)])
        if name in rel["any"]:
            return float(rel["any"][name])     # ranked in another division (a mover)
        return 99.0
