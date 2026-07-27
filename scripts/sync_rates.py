#!/usr/bin/env python3
"""Sync data/rates.json from the "KMA Rates" Google Sheet, then rebuild /rates/.

The gym edits the sheet (columns: Section, Plan, Description, Price, Popular —
one row per price card). This pulls those rows, writes data/rates.json, and runs
build_rates.py so rates/index.html regenerates. Then commit + push to deploy.

    python3 scripts/sync_rates.py

Reads the sheet via the same helper as the other syncs (service account in CI,
gws CLI locally). The sheet is the source of truth for card content.

Sheet: https://docs.google.com/spreadsheets/d/1f4IUkTTE2Kim4pO5gwore7ZV_fcnM_ghTEpx1c5nNhs/edit
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets  # local: reads via service account (CI) or gws CLI (local)

SHEET_ID = "1f4IUkTTE2Kim4pO5gwore7ZV_fcnM_ghTEpx1c5nNhs"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "rates.json"

# Sections build_rates.py knows how to render. A row with any other Section is
# kept in the data but warned about (it won't appear until added to build_rates).
KNOWN = {"Membership", "BJJ", "Judo", "Muay Thai", "Boxing", "Taekwondo", "Self-Defence"}
TRUE = {"true", "yes", "1", "x", "✓", "checked"}


def main() -> None:
    rows = sheets.get_values(SHEET_ID, "Rates!A2:E")
    cards = []
    warnings = []
    for n, row in enumerate(rows, start=2):
        section, plan, desc, price, popular = [x.strip() for x in (row + [""] * 5)[:5]]
        if not section and not plan:
            continue  # blank row
        if not section or not plan:
            warnings.append(f"row {n}: missing Section or Plan — skipped ({section!r}/{plan!r})")
            continue
        if section not in KNOWN:
            warnings.append(f"row {n}: unknown Section {section!r} — won't render until added to build_rates.py")
        cards.append({
            "section": section,
            "plan": plan,
            "description": desc,
            "price": price,
            "popular": popular.lower() in TRUE,
        })

    OUT.write_text(json.dumps({"cards": cards}, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(cards)} rate cards to {OUT.relative_to(ROOT)}")
    for w in warnings:
        print(f"  ! {w}")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_rates.py")], check=True)


if __name__ == "__main__":
    main()
