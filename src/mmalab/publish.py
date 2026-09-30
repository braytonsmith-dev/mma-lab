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
ol.fav,ul.fav{padding-left:22px}ol.fav li,ul.fav li{margin:3px 0}.flag{color:#d03b3b;font-size:.85rem}\nh3{font-size:1rem;margin:14px 0 4px}\n.tag{color:var(--ink2);margin:0 0 6px;font-size:1rem}.scroll{overflow-x:auto}table.cmp td,table.cmp th{white-space:nowrap}\nimg{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
"""


HEAD = ("<thead><tr><th>#</th><th>Fighter</th><th class='num'>Score</th><th class='num'>Rating</th>"
        "<th>Last 5</th><th class='num'>Quality wins</th><th class='num'>15-yr QW</th>"
        "<th class='num'>Days since</th><th>Stability</th></tr></thead>")


def _row(r) -> str:
    interim = bool(getattr(r, "interim", False))
    label = "C" if r.champion else ("IC" if interim else str(r.rank))
    cls = ' class="champ"' if (r.champion or interim) else ""
    last5 = getattr(r, "last5", r.record_3y)
    qw = getattr(r, "quality_wins", float("nan"))
    ent = " E" if bool(getattr(r, "entrenched", False)) else ""
    inj = " <span class='band'>(injury)</span>" if bool(getattr(r, "injury", False)) else ""
    band = "" if (r.champion or interim) else f"{int(r.rank_p10)}-{int(r.rank_p90)}"
    return (f"<tr{cls}><td>{label}</td><td>{html.escape(r.fighter)}{inj}</td>"
            f"<td class='num'>{r.score:+.2f}</td><td class='num'>{r.rating:.0f}</td>"
            f"<td>{last5}</td><td class='num'>{qw:.1f}</td>"
            f"<td class='num'>{int(r.top15_wins)}{ent}</td><td class='num'>{int(r.days_since)}</td>"
            f"<td class='band'>{band}</td></tr>")


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
            f"<p class='meta'>Curated by {html.escape(fav.get('curator', ''))}. Favorite is not the same as best: "
            f"this list reflects personal criteria, not the divisional model. Order set {fav['list_set']}; "
            f"last-five UFC records verified from the fight data through {as_of}.</p>"
            f"<ol class='fav'>{top}</ol><h3>Honorable mentions</h3><ul class='fav'>{hm}</ul>"
            f"<details><summary>Criteria</summary><ol>{crit}</ol></details>")


EXTERNAL = [("ufc_media.csv", "UFC media panel"), ("ufc_meta.csv", "Meta UFC Rankings"), ("sherdog.csv", "Sherdog")]


def comparison_section() -> str:
    """Side by side, top 15 per division: our board next to the UFC media panel, Meta and Sherdog.
    Each outside name carries our position for that fighter in grey."""
    from mmalab.compare import norm
    ext_dir = ROOT / "data" / "external"
    boards = {}
    for fname, label in EXTERNAL:
        pth = ext_dir / fname
        if pth.exists():
            d = pd.read_csv(pth)
            boards[label] = d
    if not boards:
        return ""
    ours = pd.read_csv(OUT / "composite_rankings_full.csv")
    ours["key"] = ours["fighter"].map(norm)
    our_pos = {}
    for r in ours.itertuples():
        our_pos[r.key] = ("C" if r.champion else "IC" if getattr(r, "interim", False) else f"#{r.rank}", r.division)
    as_of = {label: str(d["as_of"].max()) for label, d in boards.items()}
    parts = ["<h2 id='compare'>Side by side: our board and the public boards</h2>",
             "<p class='meta'>Top 15 contenders per division. Grey tag = our position for that fighter "
             "(\"other div\" if we rank him in another division, \"-\" if not on our board). Sherdog ranks every "
             "promotion and lists champions inside its top 10. Board dates: "
             + "; ".join(f"{k} {v}" for k, v in as_of.items()) + ".</p>"]
    for div in RANKED_DIVISIONS:
        o = ours[ours["division"] == div].sort_values("rank")
        rows_by = {"Ours": {}}
        for r in o.itertuples():
            slot = 0 if (r.champion or getattr(r, "interim", False)) else r.rank
            if slot <= 15 and slot not in rows_by["Ours"]:
                rows_by["Ours"][slot] = (r.fighter, "IC" if getattr(r, "interim", False) and not r.champion else "")
        for label, d in boards.items():
            g = d[d["division"] == div]
            rows_by[label] = {}
            for x in g.itertuples():
                if x.rank <= 15:
                    rows_by[label].setdefault(int(x.rank), (x.fighter, "IC" if str(x.is_interim) in ("1", "True") else ""))
        cols = ["Ours"] + list(boards)
        body = []
        for slot in range(0, 16):
            if all(slot not in rows_by[c] for c in cols):
                continue
            cells = []
            for c in cols:
                if slot in rows_by[c]:
                    name, tag = rows_by[c][slot]
                    extra = ""
                    if c != "Ours":
                        pos = our_pos.get(norm(name))
                        extra = f" <span class='band'>({pos[0] if pos and pos[1] == div else 'other div' if pos else '-'})</span>"
                    label_tag = f"<span class='band'>{tag} </span>" if tag else ""
                    cells.append(f"<td>{label_tag}{html.escape(name)}{extra}</td>")
                else:
                    cells.append("<td></td>")
            body.append(f"<tr><td>{'C' if slot == 0 else slot}</td>{''.join(cells)}</tr>")
        head = "<tr><th>#</th>" + "".join(f"<th>{html.escape(c)}</th>" for c in cols) + "</tr>"
        parts.append(f"<details><summary>{html.escape(div)}</summary><div class='scroll'><table class='cmp'>"
                     f"<thead>{head}</thead><tbody>{''.join(body)}</tbody></table></div></details>")
    return "\n".join(parts)


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
    wsrc = cfg["resume"]["weights"] if cfg.get("board_model") == "resume" else cfg["weights"]
    w = ", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in wsrc.items())
    site = cfg.get("site_name", "REAL Fighter Rankings")
    tagline = cfg.get("site_tagline", "")

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
<p class="tag">{html.escape(tagline)}</p>
<p class="meta"><a href="#boards">Divisional boards</a> · <a href="#compare">Side by side</a> ·
<a href="methodology.html">Methodology</a> · <a href="#favorites">Personal top ten</a> ·
<a href="#cards">Card quality</a> · <a href="#backtest">Model accuracy</a></p>
<p class="meta">Data through {as_of}. Page built {date.today()}. Weights: {w}. Stability = 10th to 90th
percentile position across {cfg['resume']['stability_draws']} weight vectors near the configured weights.
Champion (C) = last undisputed title-bout winner. Open source, public data (UFCStats).</p>
<details><summary>How the score is built</summary><p>Resume first: who has earned it as of now.
Score = 70% resume rating + 30% quality wins, each measured as distance from the division median in
interdecile ranges. The resume rating credits wins and losses by opponent strength; decisions blend the
judges' cards with the fight stats; losses to a top-3 fighter or in a title fight cost 15% (75% if
dominant, 100% for a round-one finish by a heavy favorite). Quality wins are wins over UFC fighters with
5+ UFC wins or ranked top 7 at the time, weighted by age (3, 5, 10, 15 years); a dominant loss in the last
3 years cancels one. No penalty for the first 12 months off; documented injury layoffs are exempt.
A fighter who beat someone in their latest meeting (last 3 years) and sits within 3 spots below moves
above him. E = entrenched (5+ quality wins in 15 years). Stability = 10th to 90th percentile position
across nearby weights.</p></details>
<div id='boards'></div>{board_tables(cfg)}
{comparison_section()}
{favorites_section(bouts, as_of)}
<h2 id='cards'>Card-quality index, 2022 to present</h2>
<img src="fig_card_quality.png" alt="Top-10 bouts per card, numbered vs Fight Night">
{cq}
<h2 id='backtest'>Does the rating predict?</h2>
<img src="fig_backtest.png" alt="Backtest log loss by year and calibration">
{md_table_to_html(table_md)}
<p class='meta'>Independent fan research project built on public UFCStats data. Not affiliated with, sponsored or endorsed by UFC, Zuffa, LLC, TKO Group Holdings, or any athlete. All trademarks belong to their owners and are used only to identify athletes and events.</p>
</body></html>"""
    (DOCS / "index.html").write_text(page)
    print(f"docs/index.html written (data through {as_of})")


if __name__ == "__main__":
    main()
