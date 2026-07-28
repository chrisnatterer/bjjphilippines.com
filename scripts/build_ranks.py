#!/usr/bin/env python3
"""Regenerate the coloured-belt rank pages from data/athletes.json.

Same data-driven pattern as build_roster / build_schedule / build_rates. The
belt pages (/ranks/black-belt/, /ranks/brown-belt/, /ranks/purple-belt/) used to
be hand-maintained; gradings happen ~monthly, so this generates them from the
Rank Tracker instead. build_roster.py writes athletes.json (name, currentRank,
timeline of rank→date); this script groups people by their current sub-rank and
rewrites each page's roster between <!-- RANKS:START/END --> markers. The hero,
promotion photos, header and footer stay static.

    python3 scripts/build_roster.py   # refresh athletes.json first
    python3 scripts/build_ranks.py

The sheet is the single source of truth: whoever is at a belt in the tracker
appears on that belt's page, with promotion history built from the dated
columns. Legacy names with no promotion date show as name-only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "athletes.json"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
STAR = ('<svg class="w-4 h-4 text-gold" fill="currentColor" viewBox="0 0 24 24">'
        '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>')

# Per belt: page file, the colour word used in athletes.json ranks, the base
# abbreviation for history strings, and the sub-ranks in display order (top→
# bottom, highest first). Sub-ranks with nobody are skipped.
BELTS = {
    "black": {
        "file": ROOT / "ranks" / "black-belt" / "index.html",
        "color": "Black", "abbr": "BB", "kind": "degree",
        "order": ["Black 6th Degree", "Black 5th Degree", "Black 4th Degree",
                  "Black 3rd Degree", "Black 2nd Degree", "Black 1st Degree", "Black Belt"],
    },
    "brown": {
        "file": ROOT / "ranks" / "brown-belt" / "index.html",
        "color": "Brown", "abbr": "Brown", "kind": "stripe",
        "order": ["Brown 4th Stripe", "Brown 3rd Stripe", "Brown 2nd Stripe",
                  "Brown 1st Stripe", "Brown Belt"],
    },
    "purple": {
        "file": ROOT / "ranks" / "purple-belt" / "index.html",
        "color": "Purple", "abbr": "Purple", "kind": "stripe",
        "order": ["Purple 4th Stripe", "Purple 3rd Stripe", "Purple 2nd Stripe",
                  "Purple 1st Stripe", "Purple Belt"],
    },
}


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_date(iso: str) -> str:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    if not m:
        return ""
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    return f"{MONTHS[mo - 1]} {y}" if d == 1 else f"{MONTHS[mo - 1]} {d}, {y}"


def sub_abbr(rank: str, cfg: dict) -> str:
    """'Black 2nd Degree' -> '2nd'; 'Brown Belt' -> base abbr ('Brown')."""
    parts = rank.split()
    if parts[-1] == "Belt":
        return cfg["abbr"]
    return parts[1]  # 1st / 2nd / 3rd / 4th / 5th / 6th


def history(a: dict, cfg: dict) -> str:
    """Promotion chain at this belt colour: 'Brown Mar 2022 → 1st Dec 2022'.
    A single dated rank shows just the date; no dates → empty (name only)."""
    entries = [(t["rank"], t["date"]) for t in a.get("timeline", [])
               if t["rank"].startswith(cfg["color"]) and fmt_date(t["date"])]
    if not entries:
        return ""
    if len(entries) == 1:
        return fmt_date(entries[0][1])
    return " &rarr; ".join(f"{sub_abbr(r, cfg)} {fmt_date(d)}" for r, d in entries)


def sort_key(a: dict):
    """Oldest promotion first; undated names last, alphabetical."""
    dates = [t["date"] for t in a.get("timeline", []) if re.match(r"^\d{4}-\d{2}-\d{2}$", t["date"])]
    last = max(dates) if dates else None
    return (last is None, last or "", a["name"].lower())


def grid_cell(a: dict, cfg: dict) -> str:
    h = history(a, cfg)
    hp = f'<p class="text-warm-gray text-xs mt-0.5">{h}</p>' if h else ""
    return (f'          <div class="bg-surface p-4">'
            f'<p class="font-display font-semibold text-warm-dark text-sm">{esc(a["name"])}</p>{hp}</div>')


def list_entry(a: dict, cfg: dict) -> str:
    h = history(a, cfg)
    hp = f'\n          <p class="text-warm-gray text-sm">{h}</p>' if h else ""
    return (f'        <div class="p-5">\n'
            f'          <p class="font-display font-bold text-warm-dark">{esc(a["name"])}</p>{hp}\n'
            f'        </div>')


def grid_block(cells: list[str]) -> str:
    inner = "\n".join(cells)
    return ('      <div class="bg-surface rounded-lg border border-warm-light">\n'
            '        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-warm-light">\n'
            f'{inner}\n'
            '        </div>\n'
            '      </div>')


def degree_section(rank: str, people: list[dict], cfg: dict, last: bool) -> str:
    mb = "fade-up" if last else "mb-16 fade-up"
    if rank == "Black Belt":
        badge = f'<div class="w-10 h-10 rounded-full bg-warm-dark flex items-center justify-center">{STAR}</div>'
        title = "Black Belt"
        body = grid_block([grid_cell(a, cfg) for a in people])
    else:
        deg = rank.split()[1]  # 1st / 2nd / ...
        badge = ('<div class="w-10 h-10 rounded-full bg-warm-dark flex items-center justify-center">'
                 f'<span class="text-gold font-display font-bold text-xs">{deg}</span></div>')
        title = f"{deg} Degree"
        entries = "\n".join(list_entry(a, cfg) for a in people)
        body = ('      <div class="bg-surface rounded-lg border border-warm-light divide-y divide-warm-light">\n'
                f'{entries}\n'
                '      </div>')
    return (f'    <div class="{mb}">\n'
            f'      <div class="flex items-center gap-3 mb-6">\n'
            f'        {badge}\n'
            f'        <h2 class="font-display text-2xl font-bold text-warm-dark">{title}</h2>\n'
            f'      </div>\n'
            f'{body}\n'
            f'    </div>')


def stripe_section(rank: str, people: list[dict], cfg: dict, last: bool) -> str:
    mb = "fade-up" if last else "mb-12 fade-up"
    body = grid_block([grid_cell(a, cfg) for a in people])
    if rank.endswith("Belt"):
        h2 = f'      <h2 class="font-display text-xl font-bold text-warm-dark mb-4">{rank}</h2>'
    else:
        n = int(rank.split()[1][0])  # '4th' -> 4
        dots = "".join('<span class="w-2 h-2 rounded-full bg-warm-dark"></span>' for _ in range(n))
        label = " ".join(rank.split()[1:])  # '4th Stripe'
        h2 = ('      <h2 class="font-display text-xl font-bold text-warm-dark mb-4 flex items-center gap-3">\n'
              f'        <span class="flex gap-1">{dots}</span>\n'
              f'        {label}\n'
              '      </h2>')
    return f'    <div class="{mb}">\n{h2}\n{body}\n    </div>'


def build_page(cfg: dict, athletes: list[dict]) -> tuple[str, int]:
    here = [a for a in athletes if (a.get("currentRank") or "").startswith(cfg["color"])]
    by_rank: dict[str, list[dict]] = {}
    for a in here:
        by_rank.setdefault(a["currentRank"], []).append(a)

    ranks = [r for r in cfg["order"] if by_rank.get(r)]
    parts = []
    for i, rank in enumerate(ranks):
        people = sorted(by_rank[rank], key=sort_key)
        last = i == len(ranks) - 1
        if cfg["kind"] == "degree":
            parts.append(degree_section(rank, people, cfg, last))
        else:
            parts.append(stripe_section(rank, people, cfg, last))
    return "\n\n".join(parts), len(here)


def replace_region(html: str, body: str, file: Path) -> str:
    start, end = "<!-- RANKS:START -->", "<!-- RANKS:END -->"
    if start not in html or end not in html:
        raise SystemExit(f"Markers RANKS:START/END not found in {file}")
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pat.sub(f"{start}\n\n{body}\n\n<!-- RANKS:END -->", html)


def main() -> None:
    athletes = json.loads(DATA.read_text())
    for name, cfg in BELTS.items():
        body, n = build_page(cfg, athletes)
        html = cfg["file"].read_text()
        cfg["file"].write_text(replace_region(html, body, cfg["file"]))
        print(f"Rebuilt {cfg['file'].relative_to(ROOT)} ({n} {name} belts)")


if __name__ == "__main__":
    main()
