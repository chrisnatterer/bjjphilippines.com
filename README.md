# KMA Fitness & Martial Arts — Website

Website for **KMA Fitness & Martial Arts** (bjjphilippines.com), a BJJ gym in Makati, Philippines and part of the Team Fabricio BJJ family.

## How it works

This is a **static website** — plain HTML files with styling from Tailwind CSS loaded via CDN. There is no server-side code and no database. You edit the HTML files directly and deploy them.

The only build step is a small `build.sh` script that stamps the current commit SHA into every page's footer at deploy time. Local development works without running it — the footer will display `dev` instead.

The site was originally generated with Hugo but is now maintained as plain HTML. You do not need Hugo installed.

## GitHub repository

The full source code is hosted on GitHub:

**https://github.com/chrisnatterer/bjjphilippines.com**

## Getting the code

1. Install [Git](https://git-scm.com/downloads) if you don't have it already.
2. Open a terminal and run:
   ```
   git clone https://github.com/chrisnatterer/bjjphilippines.com.git
   ```
3. This creates a `bjjphilippines.com` folder with all the website files.

## File structure

```
bjjphilippines.com/
├── index.html              ← Homepage
├── about/index.html        ← About page
├── contact/index.html      ← Contact page
├── schedule/index.html     ← Class schedule
├── coaches/                ← Coach profile pages
│   ├── index.html          ← Coaches listing
│   ├── ken-menia/
│   ├── stephen-kamphuis/
│   ├── ziggy-roces/
│   └── ...
├── ranks/                  ← Belt rank pages
│   ├── index.html          ← Ranks overview
│   ├── white-belt/
│   ├── blue-belt/
│   ├── purple-belt/
│   ├── brown-belt/
│   ├── black-belt/
│   └── juniors/
├── programs/               ← Program descriptions
│   ├── bjj/
│   ├── muay-thai/
│   ├── judo/
│   └── boxing/
├── images/                 ← All photos and images
├── favicon.ico             ← Browser tab icon
├── favicon-32x32.png
├── apple-touch-icon.png
├── sitemap.xml             ← For search engines
└── index.xml               ← RSS feed
```

## Making changes

Since this is plain HTML, you can edit any file with a text editor (VS Code, Sublime Text, Notepad++, etc.).

### Viewing locally

Just open any `index.html` file in your browser — no server needed. For example, double-click `index.html` to see the homepage.

If you want a local dev server (for cleaner URLs like `/about/` instead of `/about/index.html`), you can use Python's built-in server:

```
cd bjjphilippines.com
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

### Styling

The site uses [Tailwind CSS](https://tailwindcss.com/) loaded from a CDN (`cdn.tailwindcss.com`). All styling is done with Tailwind utility classes directly in the HTML — there are no separate CSS files to manage.

The custom color palette and fonts are configured in a `<script>` tag in each page's `<head>`:
- **Colors**: cream, terracotta, gold, warm-dark, warm-gray, etc.
- **Fonts**: Bricolage Grotesque (headings) and DM Sans (body text), loaded from Google Fonts

## Hosting & deployment

The site is currently hosted on **Cloudflare Pages**, connected to the GitHub repository. When you push changes to the `main` branch, Cloudflare automatically deploys the updated site.

### How to set up hosting yourself

You have a few options:

#### Option A: Cloudflare Pages (recommended — free)

1. Sign up at [dash.cloudflare.com](https://dash.cloudflare.com/)
2. Go to **Workers & Pages** > **Create** > **Pages** > **Connect to Git**
3. Authorize Cloudflare to access your GitHub account
4. Select the `bjjphilippines.com` repository
5. Configure the build settings:
   - **Build command**: `bash build.sh` (stamps the commit SHA into each footer)
   - **Build output directory**: `/` (the root — all files are served directly)
6. Click **Save and Deploy**
7. Cloudflare gives you a `*.pages.dev` URL immediately
8. To use a custom domain (like `bjjphilippines.com`):
   - Go to **Custom domains** in your Pages project settings
   - Add your domain and follow the DNS instructions

#### Option B: Netlify (free)

1. Sign up at [netlify.com](https://www.netlify.com/)
2. Click **Add new site** > **Import an existing project**
3. Connect your GitHub account and select the repository
4. Leave the build command empty and set publish directory to `/`
5. Deploy

#### Option C: GitHub Pages (free)

1. Go to the repository on GitHub
2. Go to **Settings** > **Pages**
3. Under **Source**, select **Deploy from a branch**
4. Choose the `main` branch and `/ (root)` folder
5. Save — the site will be live at `https://yourusername.github.io/bjjphilippines.com`

#### Option D: Any web host

Since these are just static files, you can upload the entire folder to any web hosting provider (GoDaddy, Hostinger, etc.) via FTP or their file manager.

## Domain

The domain `bjjphilippines.com` needs to be pointed to wherever you host the site. This is done through DNS settings at your domain registrar. The hosting platform you choose will give you specific instructions.

## Data-backed pages: ranks, schedule & rates

Three parts of the site are generated from Google Sheets instead of being edited by hand:

| Page | Google Sheet | Build script | Data file |
|------|--------------|--------------|-----------|
| `/roster/` (athlete search) | **KMA Rank Tracker** — [open](https://docs.google.com/spreadsheets/d/1_y3UAStU_j6pN9-pCY29ESz4Aogz0LCNtAYGOl-KZEM/edit) | `scripts/build_roster.py` | `data/athletes.json` |
| `/schedule/` (class timetable) | **KMA Class Schedule** — [open](https://docs.google.com/spreadsheets/d/1uGLeVuB3Goy1mCnbU0UgPsadHHI2JqW6ur9HwUIXtP8/edit) | `scripts/sync_schedule.py` | `data/schedule.json` |
| `/rates/` (prices) | **KMA Rates** — [open](https://docs.google.com/spreadsheets/d/1f4IUkTTE2Kim4pO5gwore7ZV_fcnM_ghTEpx1c5nNhs/edit) | `scripts/sync_rates.py` | `data/rates.json` |

### How the sync works

These pages update **automatically** — a nightly GitHub Action (~3 AM Manila) reads all three sheets, regenerates the data + pages, and pushes; Cloudflare then redeploys. So an edit in a sheet appears on the website the next morning without anyone running anything.

If you want a change to go live **immediately** instead of waiting for the nightly run, you can run the sync yourself:

1. **Run the build script locally.** This requires the [`gws` Google Workspace CLI](https://github.com/googleworkspace/google-workspace-cli), signed in to the Google account that owns the sheets:
   ```
   git pull                             # get the bot's latest first
   python3 scripts/build_roster.py      # ranks / roster
   python3 scripts/sync_schedule.py     # class schedule
   python3 scripts/sync_rates.py        # prices / rates
   ```
   Each script reads its sheet and rewrites the data file. `sync_schedule.py` and `sync_rates.py` also regenerate their page's HTML from the JSON (via `build_schedule.py` / `build_rates.py`).
2. **Commit and push the regenerated files:**
   ```
   git add data/ schedule/ rates/
   git commit -m "Sync sheets to site"
   git push
   ```
3. Cloudflare redeploys automatically and the changes go live in a minute or two.

Notes:
- `/roster/` loads `data/athletes.json` in the browser at page load. `/schedule/` and `/rates/` are baked into static HTML by the build script (better for SEO and no-JS).
- The scripts call `gws` at a pinned Homebrew path (`/opt/homebrew/Cellar/googleworkspace-cli/<version>/bin/gws`). If a Homebrew upgrade changes the version, update the `GWS` constant in `scripts/sheets.py`. Auth is stored in the system keyring.

### Editing the class schedule

Coaches edit the **KMA Class Schedule** sheet directly — one row per class (Day, Start, End, Class, Type, Coach 1, Coach 2, Note); the sheet's *How to edit* tab explains each column. The old timetable was hand-coded with pixel positions; it is now fully data-driven, so nobody needs to touch HTML to change a class.

### The black / brown / purple belt pages

These three belt pages are **generated from the same Rank Tracker sheet** — you don't edit their HTML. When someone is promoted, update their row in the Rank Tracker (put the promotion date in the right belt/stripe column); overnight the belt pages regenerate to match. Whoever is at a belt in the sheet appears on that belt's page, grouped by degree/stripe, with their promotion history. (The white, blue and juniors pages are still edited by hand for now.)

### Editing the rates / prices

The gym edits the **KMA Rates** sheet directly — one row per price card (Section, Plan, Description, Price, Popular); the sheet's *How to edit* tab explains each column. Type the price as a plain number (e.g. `3500`) — the website adds the ₱ sign and comma. Tick **Popular** to give a card the highlighted border. Section headings and the "More about …" links live in the code (`scripts/build_rates.py`), so adding a whole new sport is a developer step; everyday price and plan changes are sheet-only.

## Pushing changes

After making edits:

```
git add .
git commit -m "Describe what you changed"
git push
```

If hosting is connected to GitHub (Cloudflare Pages, Netlify, or GitHub Pages), the site will update automatically within a minute or two.
