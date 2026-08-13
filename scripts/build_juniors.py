#!/usr/bin/env python3
"""Regenerate /ranks/juniors/ from the Rank Tracker's "Juniors" tab.

Juniors are tracked separately from adults (a different tab, a different model:
one row per kid with an explicit Current Belt + Stripes, no dated columns). This
reads that tab and rebuilds the juniors roster between <!-- RANKS:START/END -->
markers, grouped by belt (Green → Orange → Yellow → White, highest first), with
stripe count shown per kid. Same nightly-sync pattern as the other pages.

    python3 scripts/build_juniors.py

Reads the sheet via scripts/sheets.py (service account in CI, gws CLI locally).
The sheet is the single source of truth — whoever is in the Juniors tab appears.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets

SHEET_ID = "1_y3UAStU_j6pN9-pCY29ESz4Aogz0LCNtAYGOl-KZEM"
ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "ranks" / "juniors" / "index.html"

# Belt display order (highest first) + its swatch classes on the page.
BELTS = [
    ("Green", "bg-green-600"),
    ("Orange", "bg-orange-500"),
    ("Yellow", "bg-yellow-400"),
    ("White", "bg-white border border-warm-light"),
]


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stripes_label(n: int) -> str:
    if n <= 0:
        return ""
    return f"{n} Stripe" if n == 1 else f"{n} Stripes"


def cell(name: str, stripes: int) -> str:
    lbl = stripes_label(stripes)
    sp = f'\n            <p class="text-warm-gray text-xs">{lbl}</p>' if lbl else ""
    return ('          <div class="bg-surface p-4">\n'
            f'            <p class="font-display font-semibold text-warm-dark text-sm">{esc(name)}</p>{sp}\n'
            '          </div>')


def section(belt: str, swatch: str, kids: list[tuple[str, int]], last: bool) -> str:
    mb = "fade-up" if last else "mb-16 fade-up"
    cells = "\n".join(cell(n, s) for n, s in kids)
    return (f'    <div class="{mb}">\n'
            '      <div class="flex items-center gap-3 mb-6">\n'
            f'        <div class="w-10 h-5 rounded-sm {swatch}"></div>\n'
            f'        <h2 class="font-display text-2xl font-bold text-warm-dark">{belt} Belt</h2>\n'
            '      </div>\n'
            '      <div class="bg-surface rounded-lg border border-warm-light">\n'
            '        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-warm-light">\n'
            f'{cells}\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>')


def main() -> None:
    rows = sheets.get_values(SHEET_ID, "Juniors!A2:D")
    by_belt: dict[str, list[tuple[str, int]]] = {}
    warnings = []
    known = {b for b, _ in BELTS}
    for n, row in enumerate(rows, start=2):
        name, belt, stripes = (list(row) + ["", "", ""])[:3]
        name = name.strip()
        if not name:
            continue
        belt = belt.strip().capitalize()
        if not belt:
            warnings.append(f"row {n}: {name!r} has no belt — skipped")
            continue
        if belt not in known:
            warnings.append(f"row {n}: {name!r} unknown belt {belt!r} — skipped")
            continue
        m = re.search(r"\d+", str(stripes))
        by_belt.setdefault(belt, []).append((name, int(m.group()) if m else 0))

    present = [(b, s) for b, s in BELTS if by_belt.get(b)]
    parts = []
    for i, (belt, swatch) in enumerate(present):
        kids = sorted(by_belt[belt], key=lambda k: (-k[1], k[0].lower()))
        parts.append(section(belt, swatch, kids, last=(i == len(present) - 1)))
    body = "\n\n".join(parts)

    html = PAGE.read_text()
    start, end = "<!-- RANKS:START -->", "<!-- RANKS:END -->"
    if start not in html or end not in html:
        raise SystemExit(f"Markers RANKS:START/END not found in {PAGE}")
    html = re.sub(re.escape(start) + r".*?" + re.escape(end),
                  f"{start}\n\n{body}\n\n<!-- RANKS:END -->", html, flags=re.S)
    PAGE.write_text(html)
    total = sum(len(v) for v in by_belt.values())
    print(f"Rebuilt {PAGE.relative_to(ROOT)} ({total} juniors across {len(present)} belts)")
    for w in warnings:
        print(f"  ! {w}")


if __name__ == "__main__":
    main()
