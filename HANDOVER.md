# Handover — bjjphilippines.com (KMA Fitness & Martial Arts)

This document is for the **new technical maintainer** taking over the website.
It covers every account and moving part, in the order you should tackle them.

The handover is planned in **two phases**:

- **Phase 1 (now):** you take over the infrastructure — GitHub, Cloudflare, the
  domain, and edit access to the Google Sheets.
- **Phase 2 (when you're ready):** you take over the nightly data sync (the
  Google Cloud service account). Until then it keeps running under the previous
  owner's Google Cloud org, unchanged.

For how the site actually works (architecture, the sheet→site pipelines), read
**`README.md`** (owner-facing) and **`CLAUDE.md`** (developer notes) first — this
file assumes that context and focuses on *access transfer*.

---

## 1. What the site is (one paragraph)

Static HTML + Tailwind (via CDN) — no build step for pages. Hosted on
**Cloudflare Pages**, which redeploys automatically on every push to `main`
(its build command is `build.sh`, which only stamps the commit SHA into
footers). Four pages are **generated from Google Sheets** by Python scripts
(`/roster/`, `/schedule/`, `/rates/`, and the `/ranks/{black,brown,purple}-belt/`
pages). A **GitHub Actions** workflow (`.github/workflows/sync-sheets.yml`) runs
those scripts **nightly (~03:00 Manila)** and pushes the regenerated files.

## 2. Accounts & access inventory

| System | Currently owned by | What it does | Phase |
|---|---|---|---|
| GitHub repo `chrisnatterer/bjjphilippines.com` | previous owner's GitHub | source of truth; push → deploy | 1 |
| Cloudflare Pages project | previous owner's Cloudflare | hosting + auto-deploy | 1 |
| Domain `bjjphilippines.com` | previous owner's registrar | DNS → Cloudflare | 1 |
| Google Sheets ×3 (Rank Tracker, Class Schedule, Rates) | `chris@globalization.guide` | the data coaches edit | 1 (edit access) / 2 (ownership) |
| Google Cloud service account `kma-sheet-sync@globalisationguideorg.iam.gserviceaccount.com` | previous owner's GCP org | nightly sheet→site sync | 2 |
| GitHub Actions secret `GOOGLE_SERVICE_ACCOUNT_JSON` | this repo's settings | auth for the nightly sync | 1 (re-add) / 2 (replace) |
| Gym Google account `bjjfp.com@gmail.com` | the gym | already an **editor** on all sheets | ✅ done |
| Contact email `mail@bjjphilippines.com` | gym-owned domain | — | ✅ not personal |

**Sheet IDs** (needed if you ever recreate them — see Phase 2):
- Rank Tracker: `1_y3UAStU_j6pN9-pCY29ESz4Aogz0LCNtAYGOl-KZEM`
- Class Schedule: `1uGLeVuB3Goy1mCnbU0UgPsadHHI2JqW6ur9HwUIXtP8`
- Rates: `1f4IUkTTE2Kim4pO5gwore7ZV_fcnM_ghTEpx1c5nNhs`

## 3. Phase 1 — take over the infrastructure

1. **GitHub repo.** Previous owner: Settings → *Transfer ownership* to the new
   GitHub account/org (or add the new maintainer as an **Admin** collaborator if
   not transferring yet). Note: **Actions secrets do not survive a transfer** —
   see step 4.
2. **Cloudflare Pages.** Two options:
   - *Simplest:* the new maintainer creates a Pages project in **their own**
     Cloudflare account, connects it to the (now transferred) GitHub repo, sets
     the build command to `bash build.sh` and output dir to the repo root, then
     adds `bjjphilippines.com` as a custom domain.
   - *Or* transfer within Cloudflare if both parties use the same account tier.
   Verify a test commit deploys before switching DNS.
3. **Domain / DNS.** `bjjphilippines.com` must resolve to the Cloudflare Pages
   project. If the domain stays at the current registrar, just point/keep the
   DNS records at the new Pages project. If transferring the registrar, do that
   too. **Also:** a secondary domain `kma.chrisnatterer.com` (the previous
   owner's personal domain) may still be attached to the old Pages project as a
   custom domain — it should be **removed** (the code no longer references it).
4. **Re-add the sync secret.** In the repo: Settings → Secrets and variables →
   Actions → add `GOOGLE_SERVICE_ACCOUNT_JSON` with the service-account key JSON
   (the previous owner provides this value — the account stays theirs during
   Phase 1). Without it the nightly job fails.
5. **Google Sheets — edit access.** Get **Editor** on all three sheets (the
   previous owner shares them, or you use `bjjfp.com@gmail.com`). Ownership stays
   with `chris@globalization.guide` until Phase 2.
6. **Verify.** Trigger the workflow manually (Actions tab → *Sync sheets to
   site* → *Run workflow*) and confirm it commits/pushes and Cloudflare deploys.

After Phase 1 the site is fully served and deployed under the new maintainer;
only the nightly sync still authenticates via the previous owner's Google Cloud.

## 4. Phase 2 — take over the nightly sync

Do this when you're ready to fully cut the previous owner's Google Cloud out.

1. **Create a Google Cloud project** in your own org; **enable the Google Sheets
   API**.
2. **Create a service account**, create a **JSON key**, download it.
3. **Share all three sheets** (Viewer is enough) with the new service account's
   email.
4. **Replace the secret** `GOOGLE_SERVICE_ACCOUNT_JSON` in the repo with the new
   key. Run the workflow manually to confirm it still syncs.
5. **Remove** the old service account
   (`kma-sheet-sync@globalisationguideorg…`) from the sheets' sharing.
6. **Sheet ownership (optional but recommended for a full cut).** Google does
   **not** allow transferring ownership from a Workspace account
   (`chris@globalization.guide`) to an external Gmail. To fully own the data:
   make a **copy** of each sheet in the target account, re-share with the gym
   editor + the new service account, and update the `SHEET_ID` constants in
   `scripts/build_roster.py`, `scripts/sync_schedule.py`, `scripts/sync_rates.py`
   (and the Rates/Schedule tab-gid references in `CLAUDE.md`). Then the old
   sheets can be retired.

## 5. Local development setup (for the maintainer)

```
git clone <repo>
pip install -r scripts/requirements.txt        # google-auth for the SA path
```

To run the sheet syncs locally you need read access to the sheets, via **either**:
- the **service account**: set `GOOGLE_SERVICE_ACCOUNT_JSON` (inline JSON) or
  `GOOGLE_APPLICATION_CREDENTIALS` (path to key file) — same as CI; **or**
- the **`gws` CLI** (Google Workspace CLI), signed into a Google account with
  access. Note `scripts/sheets.py` pins the Homebrew path
  `/opt/homebrew/Cellar/googleworkspace-cli/<version>/bin/gws` in the `GWS`
  constant — update it for your machine/version.

Run order (roster must run before the belt pages):
```
python3 scripts/build_roster.py      # → data/athletes.json
python3 scripts/build_ranks.py       # → /ranks/{black,brown,purple}-belt/
python3 scripts/sync_schedule.py     # → data/schedule.json + /schedule/
python3 scripts/sync_rates.py        # → data/rates.json + /rates/
git add data/ ranks/ schedule/ rates/ && git commit && git push
```
Everyday edits happen in the sheets; the nightly job publishes them. Run the
scripts by hand only to push a change immediately. **Always `git pull --rebase`
before pushing** — the nightly bot commits to `main`.

## 6. Still tied to the previous owner (clean up on the full cut)

- **`build.sh`** hardcodes the repo slug `github.com/chrisnatterer/bjjphilippines.com`
  in the footer commit links — update it to the new repo after transfer.
- **Google Sheets ownership** — `chris@globalization.guide` (Phase 2, §4.6).
- **Service account + GCP org** — `globalisationguideorg` (Phase 2).
- **`kma.chrisnatterer.com`** — the personal preview domain. Code references are
  already removed; just detach it from Cloudflare (§3.3).
- Contact email and the sheets' coach-editor account are already gym-owned.

## 7. Decommission checklist (for the outgoing owner)

**Safe to do after Phase 1:** nothing critical yet — keep the service account,
the `GOOGLE_SERVICE_ACCOUNT_JSON` value, and sheet ownership until Phase 2, or
the nightly sync breaks.

**After Phase 2 (full cut):**
- [ ] Remove the old service account from the three sheets' sharing.
- [ ] Delete/disable the `kma-sheet-sync` service account (and its GCP project if
      unused elsewhere).
- [ ] Detach `kma.chrisnatterer.com` from Cloudflare Pages.
- [ ] Hand over or retire the original sheets (after IDs are re-pointed).
- [ ] Remove yourself as a GitHub collaborator / confirm the transfer completed.
- [ ] Confirm the domain registrar and Cloudflare account are no longer yours.
