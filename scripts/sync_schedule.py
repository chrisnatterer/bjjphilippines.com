#!/usr/bin/env python3
"""Sync data/schedule.json from the "KMA Class Schedule" Google Sheet, then rebuild.

Coach Steven edits the sheet (columns: Day, Start, End, Class, Type, Coach 1,
Coach 2, Note). This script pulls those rows, maps the human-friendly labels to
the site's data model, writes data/schedule.json, and runs build_schedule.py so
the /schedule/ page regenerates. Then commit + push to deploy.

    python3 scripts/sync_schedule.py

Reads the sheet via the gws CLI (same auth as build_roster.py). The sheet is the
source of truth; anything typed there overwrites schedule.json on the next run.

Sheet:  https://docs.google.com/spreadsheets/d/1uGLeVuB3Goy1mCnbU0UgPsadHHI2JqW6ur9HwUIXtP8/edit
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

GWS = "/opt/homebrew/Cellar/googleworkspace-cli/0.22.5/bin/gws"
SHEET_ID = "1uGLeVuB3Goy1mCnbU0UgPsadHHI2JqW6ur9HwUIXtP8"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "schedule.json"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Human label (lower-cased) -> internal type key used by build_schedule.py
TYPE_MAP = {
    "bjj": "bjj",
    "muay thai / boxing": "striking",
    "muay thai": "striking",
    "boxing": "striking",
    "striking": "striking",
    "judo": "judo",
}

# Config Steven never touches — the grid hours and the colour/legend per type.
HOURS = {"start": 7, "end": 21}
TYPES = {
    "bjj":      {"legend": "BJJ",                "bg": "bg-terracotta/10", "border": "border-terracotta/20", "hover": "hover:border-terracotta/40", "accent": "text-terracotta"},
    "striking": {"legend": "Muay Thai / Boxing", "bg": "bg-gold/10",       "border": "border-gold/20",       "hover": "hover:border-gold/40",       "accent": "text-gold"},
    "judo":     {"legend": "Judo",               "bg": "bg-warm-dark/5",   "border": "border-warm-dark/10",  "hover": "hover:border-warm-dark/20",  "accent": "text-warm-dark"},
}


def fetch(range_a1: str) -> list[list[str]]:
    params = {"spreadsheetId": SHEET_ID, "range": range_a1, "valueRenderOption": "FORMATTED_VALUE"}
    res = subprocess.run(
        [GWS, "sheets", "spreadsheets", "values", "get", "--params", json.dumps(params)],
        capture_output=True, text=True, check=True,
    )
    out = res.stdout
    return json.loads(out[out.find("{"):]).get("values", [])


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def norm_time(t: str) -> str:
    m = re.match(r"^(\d{1,2}):(\d{2})$", t.strip())
    if not m:
        raise ValueError(f"bad time {t!r}")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def main() -> None:
    rows = fetch("Schedule!A2:H")
    coaches: dict[str, dict] = {}
    classes: list[dict] = []
    warnings: list[str] = []

    for n, row in enumerate(rows, start=2):
        day, start, end, title, typ, c1, c2, note = [x.strip() for x in (row + [""] * 8)[:8]]
        if not day and not title:
            continue  # blank row
        if day not in DAYS:
            warnings.append(f"row {n}: unknown day {day!r} — skipped")
            continue
        key = TYPE_MAP.get(typ.lower())
        if not key:
            warnings.append(f"row {n}: unknown type {typ!r} — defaulted to BJJ")
            key = "bjj"

        cs = []
        for name in (c1, c2):
            if not name:
                continue
            slug = slugify(name)
            cs.append(slug)
            if slug not in coaches:
                img = f"/images/{slug}.webp"
                coaches[slug] = {"name": name, "short": name.split()[0], "img": img}
                if not (ROOT / img.lstrip("/")).exists():
                    warnings.append(f"row {n}: coach {name!r} has no image at {img}")
                if not (ROOT / "coaches" / slug / "index.html").exists():
                    warnings.append(f"row {n}: coach {name!r} has no page at /coaches/{slug}/")

        try:
            entry = {"day": day, "start": norm_time(start), "end": norm_time(end),
                     "title": title, "type": key}
        except ValueError as e:
            warnings.append(f"row {n}: {e} — skipped")
            continue
        if note:
            entry["note"] = note
        entry["coaches"] = cs
        classes.append(entry)

    classes.sort(key=lambda c: (DAYS.index(c["day"]), c["start"]))
    data = {"meta": {"hours": HOURS, "coaches": coaches, "types": TYPES}, "classes": classes}
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    print(f"Wrote {len(classes)} classes, {len(coaches)} coaches to {OUT.relative_to(ROOT)}")
    for w in warnings:
        print(f"  ! {w}")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_schedule.py")], check=True)


if __name__ == "__main__":
    main()
