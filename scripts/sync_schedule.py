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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets  # local: reads via service account (CI) or gws CLI (local)

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
    "karate": "karate",
    "self defence": "selfdefence",
    "self defense": "selfdefence",
}

# Config Steven never touches — the grid hours and the colour/legend per type.
HOURS = {"start": 7, "end": 21}
# One entry per class type = its legend label + Tailwind colour classes. The
# colours for karate/selfdefence are default-palette placeholders (Tailwind's
# CDN generates whatever classes appear here) — swap the hue in one place to
# re-theme. BJJ=terracotta, striking=gold, judo=neutral are the brand colours.
TYPES = {
    "bjj":         {"legend": "BJJ",                "bg": "bg-terracotta/10",   "border": "border-terracotta/20",   "hover": "hover:border-terracotta/40",   "accent": "text-terracotta"},
    "striking":    {"legend": "Muay Thai / Boxing", "bg": "bg-gold/10",         "border": "border-gold/20",         "hover": "hover:border-gold/40",         "accent": "text-gold"},
    "judo":        {"legend": "Judo",               "bg": "bg-warm-dark/5",     "border": "border-warm-dark/10",    "hover": "hover:border-warm-dark/20",    "accent": "text-warm-dark"},
    "karate":      {"legend": "Karate",             "bg": "bg-emerald-700/10",  "border": "border-emerald-700/20",  "hover": "hover:border-emerald-700/40",  "accent": "text-emerald-700"},
    "selfdefence": {"legend": "Self Defence",       "bg": "bg-sky-700/10",      "border": "border-sky-700/20",      "hover": "hover:border-sky-700/40",      "accent": "text-sky-700"},
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


# Coaches type first names in the sheet ("Estie"), but profile pages and photos
# live under full-name slugs (/coaches/estie-liwanen/). Map the short slug to
# the canonical one so the schedule links and shows the photo. Names not listed
# here (e.g. Luan, Ric — no profile page yet) fall through and render as plain
# text, which sync warnings will point out.
COACH_SLUGS = {
    "estie": "estie-liwanen",
    "stephen": "stephen-kamphuis",
    "godwin": "godwin-langbayan",
    "ziggy": "ziggy-roces",
    "brendo": "brendo-pudan",
    "ken": "ken-menia",
    "mariane": "mariane-mariano",
}


def norm_time(t: str) -> str:
    m = re.match(r"^(\d{1,2}):(\d{2})$", t.strip())
    if not m:
        raise ValueError(f"bad time {t!r}")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def main() -> None:
    rows = sheets.get_values(SHEET_ID, "Schedule!A2:H")
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
            slug = COACH_SLUGS.get(slug, slug)
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
