"""
publish.py - Write docs/index.html (served by GitHub Pages) from the outputs.

One self-contained page: the composite boards per division with stability
bands, the card-quality summary, and the backtest table. No JavaScript
dependencies, so it renders anywhere and is easy to link from a Substack post.
"""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from mmalab.rankings import RANKED_DIVISIONS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"

CSS = """
:root{--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:#e1e0d9;--surface:#fcfcfb;--blue:#2a78d6}
@media (prefers-color-scheme: dark){:root{--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--surface:#1a1a19;--blue:#3987e5}}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--surface);color:var(--ink);
     margin:0;padding:24px 16px;max-width:1000px;margin-inline:auto;line-height:1.45}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:28px 0 6px}
p.meta{color:var(--muted);font-size:.85rem;margin:0 0 16px}
table{border-collapse:collapse;width:100%;font-size:.9rem;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--ink2);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em}
td.num,th.num{text-align:right}tr.champ td{font-weight:600}
.band{color:var(--muted)}details{margin:6px 0}summary{cursor:pointer;color:var(--blue)}
ol.fav,ul.fav{padding-left:22px}ol.fav li,ul.fav li{margin:3px 0}.flag{color:#d03b3b;font-size:.85rem}\nh3{font-size:1rem;margin:14px 0 4px}\nimg{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
"""


HEAD = ("<thead><tr><th>#</th><th>Fighter</th><th class='num'>Score</th><th class='num'>Rating</th>"
        "<th>Last 3 yrs</th><th class='num'>UFC bouts</th><th class='num'>Top-15 wins</th>"
        "<th class='num'>Days since</th><th>Stability</th></tr></thead>")


def _row(r) -> str:
    label = "C" if r.champion else str(r.rank)
    cls = ' class="champ"' if r.champion else ""
    return (f"<tr{cls}><td>{label}</td><td>{html.escape(r.fighter)}</td>"
            f"<td class='num'>{r.score:.3f}</td><td class='num'>{r.rating:.0f}</td>"
            f"<td>{r.record_3y}</td><td class='num'>{int(r.ufc_bouts)}</td>"
            f"<td class='num'>{int(r.top15_wins)}</td><td class='num'>{int(r.days_since)}</td>"
            f"<td class='band'>{int(r.rank_p10)}-{int(r.rank_p90)}</td></tr>")


def board_tables(cfg: dict) -> str:
    """Champion plus top 10 visible; 11 through board_size (30) behind a dropdown."""
    b = pd.read_csv(OUT / "composite_rankings_full.csv")
    top = b[b["rank"] <= cfg["board_size"]]
    parts = []
    for div in RANKED_DIVISIONS:
        g = top[top["division"] == div]
        if g.empty:
            continue
        head = "".join(_row(r) for r in g[g["rank"] <= 10].itertuples())
        rest = g[g["rank"] > 10]
        more = ""
        if not rest.empty:
            more = (f"<details><summary>Show {int(rest['rank'].min())} to {int(rest['rank'].max())}</summary>"
                    f"<table>{HEAD}<tbody>{''.join(_row(r) for r in rest.itertuples())}</tbody></table></details>")
        parts.append(f"<h2>{html.escape(div)}</h2><table>{HEAD}<tbody>{head}</tbody></table>{more}")
    return "\n".join(parts)


def last_five(bouts: pd.DataFrame, name: str) -> tuple[str, str]:
    """Last five decided UFC bouts as (W-L), plus the active streak, from the fight data."""
    m = bouts[(bouts["fighter_a"] == name) | (bouts["fighter_b"] == name)].sort_values("date")
    seq = []
    for x in m.itertuples():
        r = x.result_a if x.fighter_a == name else (1 - x.result_a if x.result_a == x.result_a else x.result_a)
        if r in (0.0, 1.0):
            seq.append("W" if r == 1.0 else "L")
    if not seq:
        return "no UFC bouts", ""
    last = seq[-5:]
    streak = 1
    for r in reversed(seq[:-1]):
        if r != seq[-1]:
            break
        streak += 1
    return f"{last.count('W')}-{last.count('L')}", f"{seq[-1]}{streak}"


def favorites_section(bouts: pd.DataFrame, as_of) -> str:
    fav_path = ROOT / "config" / "favorites.yaml"
    if not fav_path.exists():
        return ""
    fav = yaml.safe_load(fav_path.read_text())

    def line(n: str, i: int | None = None) -> str:
        rec, streak = last_five(bouts, n)
        w, l = (int(x) for x in rec.split("-")) if "-" in rec else (0, 0)
        flag = " <span class='flag'>removal risk: negative last five</span>" if (l > w and n != "Conor McGregor") else ""
        num = f"{i}. " if i else ""
        return f"<li>{num}{html.escape(n)} ({rec}) <span class='band'>streak {streak}</span>{flag}</li>"

    top = "".join(line(n) for n in fav["top_ten"])
    hm = "".join(line(n) for n in fav["honorable_mentions"])
    crit = "".join(f"<li>{html.escape(c)}</li>" for c in fav["criteria"])
    return (f"<h2 id='favorites'>{html.escape(fav['title'])}</h2>"
            f"<p class='meta'>Favorite is not the same as best. Order set {fav['list_set']}; "
            f"last-five UFC records verified from the fight data through {as_of}.</p>"
            f"<ol class='fav'>{top}</ol><h3>Honorable mentions</h3><ul class='fav'>{hm}</ul>"
            f"<details><summary>Criteria</summary><ol>{crit}</ol></details>")


def md_table_to_html(md: str) -> str:
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            tag = "th" if not in_table else "td"
            out.append("<table>" if not in_table else "")
            out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
            in_table = True
        else:
            if in_table:
                out.append("</table>")
                in_table = False
            if line.strip():
                out.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config" / "weights.yaml").read_text())
    DOCS.mkdir(exist_ok=True)
    bouts = pd.read_csv(ROOT / "data" / "processed" / "bouts.csv", parse_dates=["date"])
    as_of = bouts["date"].max().date()
    w = ", ".join(f"{k} {v:.0%}" for k, v in cfg["weights"].items())
    site = cfg.get("site_name", "The Notorious Fighter Rankings")

    summary = pd.read_csv(OUT / "card_quality_summary.csv")
    summary = summary[summary["year"] >= 2022]
    cq = summary.to_html(index=False, float_format=lambda x: f"{x:.2f}", border=0)
    table_md = (OUT / "table_backtest.md").read_text() if (OUT / "table_backtest.md").exists() else ""

    for name in ("fig_card_quality.png", "fig_backtest.png"):
        if (OUT / name).exists():
            (DOCS / name).write_bytes((OUT / name).read_bytes())

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(site)}</title><style>{CSS}</style></head><body>
<h1>{html.escape(site)}</h1>
<p class="meta"><a href="#boards">Divisional boards</a> · <a href="#favorites">Top ten favorites</a> ·
<a href="#cards">Card quality</a> · <a href="#backtest">Model accuracy</a></p>
<p class="meta">Data through {as_of}. Page built {date.today()}. Weights: {w}. Stability = 10th to 90th
percentile position across {cfg['stability_draws']} random weight vectors near the configured weights.
Champion (C) = last undisputed title-bout winner. Open source, public data (UFCStats).</p>
<details><summary>How the score is built</summary><p>Six dimensions, each percentile-ranked within the
division, then weighted: current performance-adjusted Elo (opponent quality plus in-fight dominance),
net rating change over 36 months, entrenchment (UFC tenure and wins over top-15 opponents), offensive
output, activity, and durability. Change the weights in config/weights.yaml and rerun.</p></details>
<div id='boards'></div>{board_tables(cfg)}
{favorites_section(bouts, as_of)}
<h2 id='cards'>Card-quality index, 2022 to present</h2>
<img src="fig_card_quality.png" alt="Top-10 bouts per card, numbered vs Fight Night">
{cq}
<h2 id='backtest'>Does the rating predict?</h2>
<img src="fig_backtest.png" alt="Backtest log loss by year and calibration">
{md_table_to_html(table_md)}
<p class='meta'>Independent fan research project built on public UFCStats data. Not affiliated with or endorsed by the UFC, TKO Group, or Conor McGregor.</p>
</body></html>"""
    (DOCS / "index.html").write_text(page)
    print(f"docs/index.html written (data through {as_of})")


if __name__ == "__main__":
    main()
