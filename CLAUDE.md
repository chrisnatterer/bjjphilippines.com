# KMA Fitness & Martial Arts Website

Static website for KMA Fitness & Martial Arts (bjjphilippines.com) — a BJJ gym in Makati, Philippines, part of the Team Fabricio BJJ family.

## Tech Stack
- Static HTML + Tailwind CSS (via CDN)
- No build step — files served directly
- Hosted on Cloudflare Pages

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
