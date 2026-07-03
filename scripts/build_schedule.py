#!/usr/bin/env python3
"""Regenerate the /schedule/ timetable from data/schedule.json.

The schedule page used to be hand-coded HTML with every class positioned by
exact pixel math — impossible for a non-technical person to edit safely. This
script makes the schedule *data-driven* (the same pattern as build_roster.py):
edit data/schedule.json, run this, and the desktop grid, legend, and mobile
day-list are all regenerated between marker comments in schedule/index.html.

    python3 scripts/build_schedule.py

Later: a Google Sheet -> schedule.json sync will feed this so coaches can edit
the timetable in a spreadsheet (see build_roster.py for the sheet-read pattern).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "schedule.json"
PAGE = ROOT / "schedule" / "index.html"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_FULL = {
    "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
    "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday",
}
HOUR_PX = 60  # one hour = 60px in the desktop grid

# Abbreviations used only in narrow (side-by-side) desktop blocks where the full
# title won't fit. Full title is still shown everywhere there's room, and on mobile.
ABBREV = {
    "Muay Thai / Boxing": "MT / Boxing",
}


def mins(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


# ---------------------------------------------------------------------------
# Calendar layout: split overlapping classes into side-by-side columns.
# Non-overlapping classes stay full width; only a cluster of classes that
# actually overlap in time gets divided into columns.
# ---------------------------------------------------------------------------
def layout_day(classes: list[dict]) -> list[dict]:
    evs = sorted(classes, key=lambda c: (mins(c["start"]), mins(c["end"])))
    clusters: list[list[dict]] = []
    cur: list[dict] = []
    cur_end = 0
    for c in evs:
        if cur and mins(c["start"]) < cur_end:
            cur.append(c)
            cur_end = max(cur_end, mins(c["end"]))
        else:
            if cur:
                clusters.append(cur)
            cur = [c]
            cur_end = mins(c["end"])
    if cur:
        clusters.append(cur)

    placed: list[dict] = []
    for cluster in clusters:
        lane_ends: list[int] = []
        for c in cluster:
            s, e = mins(c["start"]), mins(c["end"])
            lane = None
            for i, end in enumerate(lane_ends):
                if end <= s:
                    lane, lane_ends[i] = i, e
                    break
            if lane is None:
                lane = len(lane_ends)
                lane_ends.append(e)
            c["_col"] = lane
        for c in cluster:
            c["_ncols"] = len(lane_ends)
            placed.append(c)
    return placed


# ---------------------------------------------------------------------------
# Desktop grid
# ---------------------------------------------------------------------------
def coach_row_desktop(coaches, meta) -> str:
    parts = []
    for i, slug in enumerate(coaches):
        c = meta["coaches"][slug]
        if i > 0:
            parts.append('<span class="text-warm-gray">&</span>')
        parts.append(
            f'<img src="{c["img"]}" alt="" class="w-4 h-4 rounded-full object-cover">'
            f'<span class="text-warm-dark font-medium">{c["short"]}</span>'
        )
    return f'<div class="flex items-center gap-1.5 mt-1">{"".join(parts)}</div>'


def desktop_block(c, meta, start_h) -> str:
    t = meta["types"][c["type"]]
    top = mins(c["start"]) - start_h * 60
    height = mins(c["end"]) - mins(c["start"])
    ncols = c.get("_ncols", 1)
    col = c.get("_col", 0)

    if ncols == 1:
        pos_cls = "left-1 right-1 "
        geo = f"top: {top}px; height: {height}px;"
    else:
        w = 100.0 / ncols
        pos_cls = ""
        geo = (f"top: {top}px; height: {height}px; "
               f"left: calc({col * w:.2f}% + 2px); width: calc({w:.2f}% - 4px);")

    coaches = c.get("coaches", [])
    is_link = len(coaches) == 1
    hover = f' {t["hover"]} transition-colors' if is_link else ""
    cls = f'absolute {pos_cls}{t["bg"]} border {t["border"]} rounded p-2 text-xs{hover} overflow-hidden'

    # Narrow (split) blocks use a short title if one is available; full-width
    # blocks always show the full title.
    if ncols > 1:
        title = c.get("shortTitle") or ABBREV.get(c["title"]) or c["title"]
    else:
        title = c["title"]
    time_line = f'{c["start"]}–{c["end"]}'
    # Prefix the note (e.g. "1-on-1") only on full-width blocks; narrow split
    # columns don't have room, and the mobile view still carries the note.
    if c.get("note") and not coaches and ncols == 1:
        time_line = f'{c["note"]} &middot; {time_line}'

    third = coach_row_desktop(coaches, meta) if coaches else ""
    inner = (f'<p class="font-display font-bold text-warm-dark">{title}</p>'
             f'<p class="text-warm-gray">{time_line}</p>{third}')

    if is_link:
        return f'<a href="/coaches/{coaches[0]}/" class="{cls}" style="{geo}">{inner}</a>'
    return f'<div class="{cls}" style="{geo}">{inner}</div>'


def build_grid(data) -> str:
    meta = data["meta"]
    start_h, end_h = meta["hours"]["start"], meta["hours"]["end"]
    height = (end_h - start_h) * HOUR_PX

    labels = []
    for h in range(start_h, end_h):
        top = (h - start_h) * HOUR_PX
        labels.append(
            f'<div class="absolute w-full" style="top: {top}px;">'
            f'<span class="text-warm-gray font-display font-semibold text-sm p-2 block">{h:02d}:00</span></div>'
        )
    time_col = f'<div class="relative">{"".join(labels)}</div>'

    stripe = ('style="background-image: repeating-linear-gradient(to bottom, transparent, '
              'transparent 59px, rgba(235,228,216,0.5) 59px, rgba(235,228,216,0.5) 60px);"')

    day_cols = []
    for day in DAYS:
        day_classes = layout_day([c for c in data["classes"] if c["day"] == day])
        blocks = "".join(desktop_block(c, meta, start_h) for c in day_classes)
        day_cols.append(f'<div class="relative border-l border-warm-light/50" {stripe}>{blocks}</div>')

    return (f'<div class="grid grid-cols-8" style="height: {height}px;">'
            f'{time_col}{"".join(day_cols)}</div>')


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
def build_legend(data) -> str:
    meta = data["meta"]
    used = {c["type"] for c in data["classes"]}
    items = []
    for key, t in meta["types"].items():
        if key not in used:
            continue
        items.append(
            '<div class="flex items-center gap-2">'
            f'<div class="w-4 h-4 rounded {t["bg"]} border {t["border"]}"></div>'
            f'<span class="text-warm-gray text-sm">{t["legend"]}</span></div>'
        )
    return "".join(items)


# ---------------------------------------------------------------------------
# Mobile day list
# ---------------------------------------------------------------------------
def coach_row_mobile(coaches, meta) -> str:
    if not coaches:
        return ""
    if len(coaches) == 1:
        c = meta["coaches"][coaches[0]]
        return (f'<div class="flex items-center gap-2 mt-2">'
                f'<img src="{c["img"]}" alt="" class="w-5 h-5 rounded-full object-cover">'
                f'<span class="text-warm-gray text-sm">{c["name"]}</span></div>')
    parts = []
    for i, slug in enumerate(coaches):
        c = meta["coaches"][slug]
        if i > 0:
            parts.append('<span class="text-warm-gray text-sm">&</span>')
        parts.append(
            '<div class="flex items-center gap-1.5">'
            f'<img src="{c["img"]}" alt="" class="w-5 h-5 rounded-full object-cover">'
            f'<span class="text-warm-gray text-sm">{c["short"]}</span></div>'
        )
    return f'<div class="flex items-center gap-2 mt-2">{"".join(parts)}</div>'


def mobile_block(c, meta) -> str:
    t = meta["types"][c["type"]]
    coaches = c.get("coaches", [])
    is_link = len(coaches) == 1
    base = f'{t["bg"]} border {t["border"]} rounded-lg p-4'
    cls = f'{base} block {t["hover"]} transition-colors' if is_link else base

    title = c["title"] + (f' {c["note"]}' if c.get("note") else "")
    inner = (f'<span class="{t["accent"]} font-display font-semibold text-sm">{c["start"]} – {c["end"]}</span>'
             f'<p class="font-display font-bold text-warm-dark mt-1">{title}</p>'
             f'{coach_row_mobile(coaches, meta)}')

    if is_link:
        return f'<a href="/coaches/{coaches[0]}/" class="{cls}">{inner}</a>'
    return f'<div class="{cls}">{inner}</div>'


def build_mobile(data) -> str:
    meta = data["meta"]
    sections = []
    for day in DAYS:
        day_classes = sorted(
            [c for c in data["classes"] if c["day"] == day],
            key=lambda c: mins(c["start"]),
        )
        if not day_classes:
            continue
        blocks = "".join(mobile_block(c, meta) for c in day_classes)
        sections.append(
            '<div class="mb-8 fade-up">'
            f'<h2 class="font-display text-2xl font-bold text-warm-dark mb-4 pb-3 border-b-2 border-terracotta/20">{DAY_FULL[day]}</h2>'
            f'<div class="space-y-2">{blocks}</div></div>'
        )
    return "".join(sections)


# ---------------------------------------------------------------------------
def replace_region(html: str, name: str, body: str) -> str:
    start, end = f"<!-- SCHEDULE:{name}:START -->", f"<!-- SCHEDULE:{name}:END -->"
    if start not in html or end not in html:
        raise SystemExit(f"Marker {name} not found in {PAGE}")
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pat.sub(f"{start}\n{body}\n      {end}", html)


def main() -> None:
    data = json.loads(DATA.read_text())
    html = PAGE.read_text()
    html = replace_region(html, "GRID", build_grid(data))
    html = replace_region(html, "LEGEND", build_legend(data))
    html = replace_region(html, "MOBILE", build_mobile(data))
    PAGE.write_text(html)
    print(f"Rebuilt {PAGE.relative_to(ROOT)} from {DATA.relative_to(ROOT)} "
          f"({len(data['classes'])} classes)")


if __name__ == "__main__":
    main()
