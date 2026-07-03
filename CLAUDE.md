# KMA Fitness & Martial Arts Website

Static website for KMA Fitness & Martial Arts (bjjphilippines.com) — a BJJ gym in Makati, Philippines, part of the Team Fabricio BJJ family.

## Tech Stack
- Static HTML + Tailwind CSS (via CDN)
- No compile step for pages — HTML is served directly. `build.sh` only stamps the commit SHA into footers at deploy time.
- Two pages are generated from Google Sheets by local Python scripts (see **Data sync** below).
- Hosted on Cloudflare Pages (auto-deploys on push to `main`).

## Data sync — ranks & schedule

Two pages are backed by Google Sheets. **The sync is a MANUAL local step — Cloudflare does NOT run it** (its build only runs `build.sh`). Editing a sheet does nothing until someone runs the script, commits the regenerated files, and pushes.

| Page | Sheet | Script | Data file | Notes |
|------|-------|--------|-----------|-------|
| `/roster/` | KMA Rank Tracker (`1_y3UAStU...`) | `scripts/build_roster.py` | `data/athletes.json` | roster page fetches the JSON client-side |
| `/schedule/` | KMA Class Schedule (`1uGLeVuB3Goy1mCnbU0UgPsadHHI2JqW6ur9HwUIXtP8`) | `scripts/sync_schedule.py` | `data/schedule.json` | sync writes JSON then runs `build_schedule.py`, which regenerates the static grid + mobile list in `schedule/index.html` between `<!-- SCHEDULE:* -->` markers |

Both scripts read their sheet via the `gws` CLI (pinned path `/opt/homebrew/Cellar/googleworkspace-cli/<ver>/bin/gws`, auth in system keyring — update the `GWS` constant if a brew upgrade changes the version). Workflow: run script → `git add data/ schedule/` → commit → push → Cloudflare deploys. No automation exists yet. Full owner-facing docs in `README.md`.

## Structure
- `/ranks/` — Belt rank pages (white, blue, purple, brown, black, juniors)
- `/coaches/` — Coach profiles
- `/schedule/` — Class schedule
- `/about/`, `/contact/` — Info pages
- `/images/` — Photos

## Rank Tracker Spreadsheet

All athlete rank data is also maintained in a Google Sheet:

**https://docs.google.com/spreadsheets/d/1_y3UAStU_j6pN9-pCY29ESz4Aogz0LCNtAYGOl-KZEM/edit**

### Adults tab (columns)
| Columns | Content |
|---------|---------|
| A | Full Name |
| B | Location/Affiliation (e.g., Davao, Bicol, XFC Fabricio Butuan) |
| C | Status (Active/Inactive) |
| D-H | White Belt, 1st-4th Stripe |
| I-M | Blue Belt, 1st-4th Stripe |
| N-R | Purple Belt, 1st-4th Stripe |
| S-W | Brown Belt, 1st-4th Stripe |
| X-AD | Black Belt, 1st-6th Degree |
| AE | Current Rank (derived from rightmost filled rank column) |
| AF | Notes |

### Juniors tab (columns)
| Column | Content |
|--------|---------|
| A | Full Name |
| B | Current Belt (Green/Orange/Yellow) |
| C | Stripes |
| D | Notes |

### Data notes
- Initially populated 2026-04-03 by parsing the HTML rank pages
- Date formats are inconsistent (carried over from the website) — mix of "June 23", "June 2023", "October 6, 2024"
- The spreadsheet is the intended source of truth going forward; the website rank pages may be regenerated from it
- Sync mechanism is documented under **Data sync** above (manual `python3 scripts/build_roster.py` → commit → push)
