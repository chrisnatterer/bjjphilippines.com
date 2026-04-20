#!/usr/bin/env python3
"""Build /data/athletes.json from the KMA Rank Tracker Adults tab.

Reads the live sheet via the gws CLI (Google Workspace CLI) and produces a
compact JSON file that the /roster/ search page fetches client-side.

Later: swap the data source to a published-to-web CSV URL so this can run in CI
without local auth. For now, run manually before each deploy:

    python3 scripts/build_roster.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

GWS = "/opt/homebrew/Cellar/googleworkspace-cli/0.22.5/bin/gws"
SHEET_ID = "1_y3UAStU_j6pN9-pCY29ESz4Aogz0LCNtAYGOl-KZEM"
OUT = Path(__file__).resolve().parent.parent / "data" / "athletes.json"

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fetch_values(range_a1: str) -> list[list[str]]:
    params = {
        "spreadsheetId": SHEET_ID,
        "range": range_a1,
        "valueRenderOption": "FORMATTED_VALUE",
    }
    res = subprocess.run(
        [GWS, "sheets", "spreadsheets", "values", "get", "--params", json.dumps(params)],
        capture_output=True, text=True, check=True,
    )
    idx = res.stdout.find("{")
    return json.loads(res.stdout[idx:]).get("values", [])


def main() -> None:
    rows = fetch_values("Adults!A1:AG")
    header = rows[0]
    # Schema (post user's column-D move): A=Name, B=Location, C=Status,
    # D=Current Rank, E..AE=rank dates (27 cols), AF=Notes, AG=Current Rank Date.
    date_headers = header[4:31]  # E through AE inclusive

    athletes = []
    for row in rows[1:]:
        row = row + [""] * (len(header) - len(row))
        name = row[0].strip()
        current_rank = row[3].strip()
        if not name or not current_rank:
            continue  # skip name-only rows and anything missing a rank

        timeline = []
        for i, col_name in enumerate(date_headers):
            cell = row[4 + i].strip()
            if ISO_RE.match(cell):
                timeline.append({"rank": col_name, "date": cell})

        current_date = row[32].strip() if len(row) > 32 else ""
        if not ISO_RE.match(current_date):
            current_date = ""

        athletes.append({
            "name": name,
            "location": row[1].strip(),
            "status": row[2].strip() or "Active",
            "currentRank": current_rank,
            "currentRankDate": current_date,
            "timeline": timeline,
        })

    athletes.sort(key=lambda a: a["name"].lower())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Minified — this file is fetched by every visitor
    OUT.write_text(json.dumps(athletes, separators=(",", ":")))
    print(f"Wrote {len(athletes)} athletes to {OUT}")
    print(f"File size: {OUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
