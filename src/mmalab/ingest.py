"""
ingest.py - Load raw UFCStats CSVs (Greco1899/scrape_ufc_stats format) and
produce three clean tables:

    data/processed/bouts.csv        one row per bout (fighter A / fighter B, winner, method, date, division)
    data/processed/round_stats.csv  one row per fighter per round (numeric)
    data/processed/fighters.csv     tale of the tape (height, reach, stance, DOB)

Why this layer exists: every downstream module (Elo, features, rankings,
card quality) reads these three files and nothing else, so a change in the
scraper only ever touches this file.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
PROC = Path(__file__).resolve().parents[2] / "data" / "processed"

DIVISIONS = [
    "Women's Strawweight", "Women's Flyweight", "Women's Bantamweight", "Women's Featherweight",
    "Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight",
    "Middleweight", "Light Heavyweight", "Heavyweight",
]
# Order matters: check women's first so "Women's Flyweight" is not read as "Flyweight".
_DIV_PATTERNS = [(d, re.compile(re.escape(d), re.I)) for d in DIVISIONS]


def parse_division(weightclass: str) -> str:
    wc = (weightclass or "").strip()
    for name, pat in _DIV_PATTERNS:
        if pat.search(wc):
            return name
    if "catch" in wc.lower():
        return "Catch Weight"
    if "open" in wc.lower():
        return "Open Weight"
    return "Unknown"


def parse_method(method: str) -> str:
    m = (method or "").strip().lower()
    if m.startswith("ko/tko") or "doctor" in m:
        return "KO/TKO"
    if m.startswith("submission"):
        return "SUB"
    if m.startswith("decision - unanimous"):
        return "U-DEC"
    if m.startswith("decision - split"):
        return "S-DEC"
    if m.startswith("decision - majority"):
        return "M-DEC"
    if m.startswith("dq"):
        return "DQ"
    if "overturned" in m or "could not continue" in m:
        return "NC"
    return "OTHER"


def _of(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Split '29 of 73' into (29, 73)."""
    parts = series.astype(str).str.extract(r"(\d+)\s+of\s+(\d+)")
    return (pd.to_numeric(parts[0], errors="coerce").fillna(0).astype(int),
            pd.to_numeric(parts[1], errors="coerce").fillna(0).astype(int))


def _mmss(series: pd.Series) -> pd.Series:
    """'4:32' -> 272 seconds. '--' -> 0."""
    parts = series.astype(str).str.extract(r"(\d+):(\d+)")
    return (pd.to_numeric(parts[0], errors="coerce").fillna(0) * 60
            + pd.to_numeric(parts[1], errors="coerce").fillna(0)).astype(int)


def _inches(series: pd.Series) -> pd.Series:
    """5' 11" -> 71 ; 72" -> 72 ; '--' -> NaN"""
    s = series.astype(str)
    ft = s.str.extract(r"(\d+)'\s*(\d+)")
    inches_only = s.str.extract(r"^(\d+)\"")[0]
    out = pd.to_numeric(ft[0], errors="coerce") * 12 + pd.to_numeric(ft[1], errors="coerce")
    out = out.fillna(pd.to_numeric(inches_only, errors="coerce"))
    return out


def build_bouts() -> pd.DataFrame:
    res = pd.read_csv(RAW / "ufc_fight_results.csv")
    res.columns = [c.strip() for c in res.columns]
    for c in ["EVENT", "BOUT", "OUTCOME", "WEIGHTCLASS", "METHOD"]:
        res[c] = res[c].astype(str).str.strip()

    ev = pd.read_csv(RAW / "ufc_event_details.csv")
    ev.columns = [c.strip() for c in ev.columns]
    ev["EVENT"] = ev["EVENT"].astype(str).str.strip()
    ev["date"] = pd.to_datetime(ev["DATE"], format="%B %d, %Y", errors="coerce")
    ev = ev.rename(columns={"LOCATION": "location", "URL": "event_url"})[["EVENT", "date", "location", "event_url"]]

    # Known naming mismatches between the results file and the events file.
    EVENT_ALIASES = {
        "UFC Fight Night: Grasso vs. Shevchenko 2": "Noche UFC: Grasso vs. Shevchenko 2",
        "UFC Fight Night: Lopes vs. Silva": "Noche UFC: Lopes vs. Silva",
    }
    res["EVENT"] = res["EVENT"].replace(EVENT_ALIASES)
    df = res.merge(ev, on="EVENT", how="left")
    # Road to UFC 4.6 (Shanghai, Aug 2025 finals) is absent from the events file.
    mask = df["date"].isna() & df["EVENT"].str.contains("Road to UFC 4", case=False)
    df.loc[mask, "date"] = pd.Timestamp("2025-08-23")
    df.loc[mask, "location"] = "Shanghai, China"
    names = df["BOUT"].str.split(r"\s+vs\.\s+", n=1, expand=True, regex=True)
    df["fighter_a"] = names[0].str.strip()
    df["fighter_b"] = names[1].str.strip()

    # OUTCOME is from fighter_a's perspective: W/L means A won.
    out = df["OUTCOME"].str.upper()
    df["result_a"] = np.select(
        [out.eq("W/L"), out.eq("L/W"), out.eq("D/D")],
        [1.0, 0.0, 0.5], default=np.nan)          # NaN = no contest
    df["division"] = df["WEIGHTCLASS"].map(parse_division)
    df["title_fight"] = df["WEIGHTCLASS"].str.contains("Title", case=False, na=False) & \
        df["WEIGHTCLASS"].str.contains("UFC", case=False, na=False)
    df["interim"] = df["WEIGHTCLASS"].str.contains("Interim", case=False, na=False)
    df["method"] = df["METHOD"].map(parse_method)
    df["round"] = pd.to_numeric(df["ROUND"], errors="coerce")
    df["time_sec"] = _mmss(df["TIME"])
    df["sched_rounds"] = pd.to_numeric(
        df["TIME FORMAT"].astype(str).str.extract(r"^(\d+)")[0], errors="coerce")
    df["fight_seconds"] = (df["round"].fillna(1) - 1) * 300 + df["time_sec"]
    df["finish"] = df["method"].isin(["KO/TKO", "SUB"])
    df["bout_url"] = df["URL"]
    df["event"] = df["EVENT"]
    df["is_numbered"] = df["event"].str.match(r"^UFC \d+")

    cols = ["event", "date", "location", "is_numbered", "division", "title_fight", "interim",
            "fighter_a", "fighter_b", "result_a", "method", "round", "time_sec",
            "sched_rounds", "fight_seconds", "finish", "bout_url", "event_url"]
    df = df[cols].sort_values(["date", "event", "bout_url"]).reset_index(drop=True)
    df["bout_id"] = np.arange(len(df))
    return df


def build_round_stats() -> pd.DataFrame:
    s = pd.read_csv(RAW / "ufc_fight_stats.csv")
    s.columns = [c.strip() for c in s.columns]
    for c in ["EVENT", "BOUT", "FIGHTER"]:
        s[c] = s[c].astype(str).str.strip()
    out = pd.DataFrame({
        "event": s["EVENT"], "bout": s["BOUT"], "fighter": s["FIGHTER"],
        "round": pd.to_numeric(s["ROUND"].str.extract(r"(\d+)")[0], errors="coerce"),
        "kd": pd.to_numeric(s["KD"], errors="coerce").fillna(0).astype(int),
        "sub_att": pd.to_numeric(s["SUB.ATT"], errors="coerce").fillna(0).astype(int),
        "rev": pd.to_numeric(s["REV."], errors="coerce").fillna(0).astype(int),
        "ctrl_sec": _mmss(s["CTRL"]),
    })
    out["sig_landed"], out["sig_att"] = _of(s["SIG.STR."])
    out["tot_landed"], out["tot_att"] = _of(s["TOTAL STR."])
    out["td_landed"], out["td_att"] = _of(s["TD"])
    out["head_landed"], _ = _of(s["HEAD"])
    out["body_landed"], _ = _of(s["BODY"])
    out["leg_landed"], _ = _of(s["LEG"])
    out["dist_landed"], _ = _of(s["DISTANCE"])
    out["clinch_landed"], _ = _of(s["CLINCH"])
    out["ground_landed"], _ = _of(s["GROUND"])
    return out


def build_fighters() -> pd.DataFrame:
    t = pd.read_csv(RAW / "ufc_fighter_tott.csv")
    t.columns = [c.strip() for c in t.columns]
    f = pd.DataFrame({
        "fighter": t["FIGHTER"].astype(str).str.strip(),
        "height_in": _inches(t["HEIGHT"]),
        "reach_in": pd.to_numeric(t["REACH"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"),
        "weight_lb": pd.to_numeric(t["WEIGHT"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"),
        "stance": t["STANCE"].fillna("").astype(str).str.strip().replace("", np.nan),
        "dob": pd.to_datetime(t["DOB"], format="%b %d, %Y", errors="coerce"),
        "fighter_url": t["URL"],
    })
    return f.drop_duplicates("fighter", keep="first").reset_index(drop=True)


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    bouts = build_bouts()
    rounds = build_round_stats()
    fighters = build_fighters()
    bouts.to_csv(PROC / "bouts.csv", index=False)
    rounds.to_csv(PROC / "round_stats.csv", index=False)
    fighters.to_csv(PROC / "fighters.csv", index=False)
    print(f"bouts: {len(bouts):,}  ({bouts['date'].min().date()} to {bouts['date'].max().date()})")
    print(f"  no-contests dropped later: {bouts['result_a'].isna().sum()}, draws: {(bouts['result_a']==0.5).sum()}")
    print(f"  unmatched event dates: {bouts['date'].isna().sum()}")
    print(f"round_stats: {len(rounds):,} rows;  fighters: {len(fighters):,}")
    print(bouts["division"].value_counts().to_string())


if __name__ == "__main__":
    main()
