#!/usr/bin/env python3
"""Regenerate the /rates/ pricing sections from data/rates.json.

Same pattern as build_schedule.py: the rates page is data-driven. A coach edits
the "KMA Rates" Google Sheet (one row per price card: Section, Plan, Description,
Price, Popular); sync_rates.py pulls it into data/rates.json; this script rebuilds
the pricing block in rates/index.html between the <!-- RATES:START/END --> markers.

    python3 scripts/build_rates.py

Only the *card content* (plan name, description, price, which card is "Popular")
comes from the sheet. Section structure — the kicker label, heading, program-page
link, order, and background — lives here in SECTIONS. Adding a whole new sport is
a code change here (plus a /programs/<slug>/ page); everyday edits are sheet-only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "rates.json"
PAGE = ROOT / "rates" / "index.html"

# Section render config, in display order. "Membership" is special (a single
# full-width card at the top); the rest are art sections with a card grid.
MEMBERSHIP = {"kicker": "One-Time Membership", "sublabel": "Adults & Kids"}
SECTIONS = [
    {"key": "BJJ",          "kicker": "Brazilian Jiu-Jitsu", "heading": "BJJ Training",           "link": "/programs/bjj/"},
    {"key": "Judo",         "kicker": "Judo",                "heading": "Judo Training",          "link": "/programs/judo/"},
    {"key": "Muay Thai",    "kicker": "Muay Thai",           "heading": "Muay Thai Training",     "link": "/programs/muay-thai/"},
    {"key": "Boxing",       "kicker": "Boxing",              "heading": "Boxing Training",        "link": "/programs/boxing/"},
    {"key": "Taekwondo",    "kicker": "Taekwondo",           "heading": "Kids Taekwondo",         "link": "/programs/taekwondo/"},
    {"key": "Self-Defence", "kicker": "Self-Defence",        "heading": "Self-Defence Training",  "link": "/programs/self-defence/"},
]

GRID_BY_COUNT = {
    1: "grid grid-cols-1 gap-6 fade-up max-w-sm mx-auto",
    2: "grid grid-cols-1 sm:grid-cols-2 gap-6 fade-up",
    3: "grid grid-cols-1 sm:grid-cols-3 gap-6 fade-up",
}
MAXW_BY_COUNT = {1: "max-w-3xl", 2: "max-w-4xl", 3: "max-w-5xl"}


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_price(p) -> str:
    """1950 -> ₱1,950. Non-numeric values (e.g. "Free") pass through unchanged."""
    s = str(p).strip()
    num = re.sub(r"[₱,\s]", "", s)
    if re.fullmatch(r"\d+(\.\d+)?", num):
        n = float(num)
        return f"₱{int(n):,}" if n == int(n) else f"₱{n:,.2f}"
    return esc(s)


def card_html(c: dict) -> str:
    plan, desc, price = esc(c["plan"]), esc(c["description"]), fmt_price(c["price"])
    if c.get("popular"):
        return (
            '<div class="bg-surface rounded-lg p-8 border-2 border-terracotta text-center relative">'
            '<span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-terracotta text-cream text-xs '
            'font-display font-bold uppercase tracking-wider px-3 py-1 rounded-full">Popular</span>'
            f'<h3 class="font-display font-bold text-warm-dark text-lg mb-2">{plan}</h3>'
            f'<p class="text-warm-gray text-sm mb-4">{desc}</p>'
            f'<p class="text-terracotta font-display font-bold text-2xl">{price}</p></div>'
        )
    return (
        '<div class="bg-surface rounded-lg p-8 border border-warm-light text-center">'
        f'<h3 class="font-display font-bold text-warm-dark text-lg mb-2">{plan}</h3>'
        f'<p class="text-warm-gray text-sm mb-4">{desc}</p>'
        f'<p class="text-terracotta font-display font-bold text-2xl">{price}</p></div>'
    )


def membership_section(card: dict) -> str:
    plan, desc, price = esc(card["plan"]), esc(card["description"]), fmt_price(card["price"])
    return (
        '<section class="py-16 bg-cream">\n'
        '  <div class="max-w-4xl mx-auto px-5 sm:px-8 lg:px-12">\n'
        '    <div class="bg-surface rounded-lg p-8 border border-warm-light fade-up grid grid-cols-1 md:grid-cols-5 gap-6 items-center">\n'
        '      <div class="md:col-span-3">\n'
        f'        <p class="text-terracotta font-display font-semibold text-sm uppercase tracking-[0.2em] mb-2">{MEMBERSHIP["kicker"]}</p>\n'
        f'        <h2 class="font-display text-2xl sm:text-3xl font-bold text-warm-dark mb-3">{plan}</h2>\n'
        f'        <p class="text-warm-gray leading-relaxed">{desc}</p>\n'
        '      </div>\n'
        '      <div class="md:col-span-2 text-center md:text-right">\n'
        f'        <p class="text-warm-gray-light text-sm uppercase font-display tracking-[0.15em] mb-1">{MEMBERSHIP["sublabel"]}</p>\n'
        f'        <p class="text-terracotta font-display font-bold text-5xl">{price}</p>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>'
    )


def art_section(cfg: dict, cards: list[dict], warm: bool) -> str:
    n = len(cards)
    grid = GRID_BY_COUNT.get(n, "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 fade-up")
    maxw = MAXW_BY_COUNT.get(n, "max-w-5xl")
    bg = "bg-warm-light grain" if warm else "bg-cream"
    cards_html = "\n      ".join(card_html(c) for c in cards)
    return (
        f'<section class="py-16 {bg}">\n'
        f'  <div class="{maxw} mx-auto px-5 sm:px-8 lg:px-12">\n'
        '    <div class="text-center mb-10 fade-up">\n'
        f'      <p class="text-terracotta font-display font-semibold text-sm uppercase tracking-[0.2em] mb-3">{esc(cfg["kicker"])}</p>\n'
        f'      <h2 class="font-display text-3xl sm:text-4xl font-bold text-warm-dark">{esc(cfg["heading"])}</h2>\n'
        '    </div>\n'
        f'    <div class="{grid}">\n'
        f'      {cards_html}\n'
        '    </div>\n'
        f'    <p class="text-center mt-6 fade-up"><a href="{cfg["link"]}" class="text-warm-gray hover:text-terracotta text-sm transition-colors duration-300">More about {esc(cfg["key"])} training →</a></p>\n'
        '  </div>\n'
        '</section>'
    )


def build_rates(data: dict) -> str:
    cards = data["cards"]
    by_section: dict[str, list[dict]] = {}
    for c in cards:
        by_section.setdefault(c["section"], []).append(c)

    parts = []
    # Membership first, if present.
    for c in by_section.get("Membership", []):
        parts.append(membership_section(c))

    # Art sections in config order; skip any with no cards. Background alternates
    # (warm-light, cream, …) across the art sections that actually render.
    warm = True
    for cfg in SECTIONS:
        sec_cards = by_section.get(cfg["key"])
        if not sec_cards:
            continue
        parts.append(art_section(cfg, sec_cards, warm))
        warm = not warm

    return "\n\n".join(parts)


def replace_region(html: str, body: str) -> str:
    start, end = "<!-- RATES:START -->", "<!-- RATES:END -->"
    if start not in html or end not in html:
        raise SystemExit(f"Markers RATES:START/END not found in {PAGE}")
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pat.sub(f"{start}\n{body}\n<!-- RATES:END -->", html)


def main() -> None:
    data = json.loads(DATA.read_text())
    html = PAGE.read_text()
    html = replace_region(html, build_rates(data))
    PAGE.write_text(html)
    print(f"Rebuilt {PAGE.relative_to(ROOT)} from {DATA.relative_to(ROOT)} "
          f"({len(data['cards'])} cards)")


if __name__ == "__main__":
    main()
