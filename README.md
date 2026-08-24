# On2Cook Ambassador Network

An interactive portal that shows On2Cook's brand ambassadors on a map of
India: select a state, select a city, browse the roster, filter by multiple
states/cities at once, search by name/brand/code/city/state, and open a full
profile for each ambassador. Built to brand spec — Red `#FF0000` / Black
`#000000` / White `#FFFFFF` only, Montserrat for display type, DIN Next for
body/data — fully responsive, no external CDN or font dependency.

```
index.html               Markup
css/styles.css            All styling (brand colors + type as CSS variables)
js/icons.js                Small inline SVG icon set (no icon-font/CDN dependency)
js/app.js                  All interaction logic (map, filters, search, pagination, modal)
js/india-map-data.js       Static India state/UT path data for the map
js/ambassadors-data.js     Auto-generated data fallback (see below)
data/ambassadors.json      Auto-generated data (see below)
assets/fonts/               Montserrat + DIN Next, subset to woff2
assets/logo.png              (put your logo here — see "Adding your logo")
scripts/sync_sheet.py      Pulls your Google Sheet and rebuilds the data files
.github/workflows/sync-sheet.yml   Scheduled sync + GitHub Pages deploy
```

## 1. Test it right now

This zip ships with **sample/placeholder ambassador data** (82 fake records,
including example values for the optional "bonus" fields — see below) so you
can open `index.html` directly and see everything working: map, filters,
search, pagination, and the full profile modal.

> Double-clicking `index.html` works via the `js/ambassadors-data.js`
> fallback. For the more realistic test, serve the folder instead:
> ```
> python3 -m http.server 8000
> ```
> then open `http://localhost:8000`.

## 2. Adding your logo

Drop a file at **`assets/logo.png`** (square, transparent background,
roughly 64x64 to 128x128px works well — `.svg` also fine, just update the
`src` in `index.html`'s `<img>` tag if you use a different filename). It
appears automatically in the header next to the wordmark. Until you add it,
that slot just stays empty and the text wordmark carries the header on its
own — nothing breaks either way.

A `assets/favicon.ico` works the same way (silently ignored if absent).

## 3. Search & filters

- The search box (header, top right) matches **name, brand, ambassador
  code, city, or state** — type an ambassador code and it'll find it.
- The **Filters** button opens a wider panel: a quick-search field at the
  top (synced with the header search box), then two independent,
  multi-select checklists side by side — **State** and **City** — each
  with its own mini search so long lists are easy to scan. Check as many
  as you like in either list and the roster updates live. Active filters
  also show as removable chips at the top of the panel; the badge on the
  Filters button shows how many are active; **Clear all** resets
  everything.
- The coverage map shows each state's ambassador count as a small number
  badge directly on the state — no separate "states by count" list needed.
  Click a state (on the map, or its badge) to drive the guided state ->
  city drill-down instead of the filter panel; doing so clears any active
  filters/search so the two modes don't fight each other.

## 4. Your Google Sheet — required vs. optional columns

Your original headers map straight onto the portal and are all that's
required:

| Sheet column     | Used as                              |
|-------------------|---------------------------------------|
| Sr. No.           | sort order / id                       |
| Name              | ambassador name                       |
| Brand Name        | shown under the name                  |
| Billing Name      | shown in the profile modal only       |
| Ambassador Code   | badge code (searchable)               |
| City              | drives city filters/chips              |
| State             | drives the map + state filters         |
| Contact Number    | shown in the profile (Phone) and powers WhatsApp |
| E-mail            | shown in the profile                  |
| Profile           | shown as the "About" bio in the modal  |

**Optional bonus columns** — the richer profile layout (stat boxes,
specialties tags, kitchen photo, socials, etc.) only shows sections for data
that actually exists. Add any of these columns to your sheet whenever you're
ready and the portal picks them up automatically; leave them out and those
sections simply don't render:

| Optional column      | Shows up as                                  |
|------------------------|-----------------------------------------------|
| Instagram / Facebook  | "Connect" links in the profile                 |
| WhatsApp              | powers the "Contact on WhatsApp" button (falls back to Contact Number if this column is absent) |
| Kitchen Type          | e.g. "Cloud Kitchen"                           |
| Operational Since     | e.g. "2021"                                    |
| Services Offered      | comma-separated, e.g. "Catering, Delivery"     |
| Coverage Areas        | comma-separated                                |
| Specialties           | shown as tag pills                             |
| Happy Customers       | stat box                                       |
| Dishes Served         | stat box                                       |
| Rating                | stat box                                       |
| Profile URL           | powers the "View Profile" button               |
| Photo URL             | kitchen/brand photo (placeholder shown if absent) |

Column matching is tolerant of case, spacing and punctuation (e.g. "Photo
URL", "photo url", "Photo Url" all match), so you don't need exact casing.

## 5. Connect the live sheet

1. In Google Sheets: **File -> Share -> Publish to web**.
2. Pick the correct tab, format **Comma-separated values (.csv)**, click **Publish**.
3. Copy the generated link (ends in `output=csv`).
4. Run the sync locally to test it:
   ```
   export GOOGLE_SHEET_CSV_URL="paste-the-link-here"
   python3 scripts/sync_sheet.py
   ```
   This rewrites `data/ambassadors.json` and `js/ambassadors-data.js` from
   your live sheet.

## 6. Automate it with GitHub Actions

`.github/workflows/sync-sheet.yml` is already wired up to:

- Run every 6 hours (or on demand via **Actions -> Run workflow**), and on every push to `main`.
- Pull the sheet via `scripts/sync_sheet.py`.
- Commit the refreshed data files back to the repo if anything changed.
- Publish the whole site to **GitHub Pages**.

To turn it on:

1. Push this project to a GitHub repo.
2. **Settings -> Secrets and variables -> Actions -> New repository secret** ->
   name it `GOOGLE_SHEET_CSV_URL`, paste your published CSV link.
3. Contact Number and E-mail are included by default (see the note below).
   If you'd rather leave them out, add a repo **Variable**
   `INCLUDE_CONTACT_INFO` = `false`.
4. **Settings -> Pages** -> set source to **GitHub Actions**.
5. Push to `main`, or run the workflow manually once from the **Actions** tab.

From then on, editing the sheet is enough — the site updates itself.

## A note on Contact Number / E-mail

Phone and email are included in the published data by default, so they show
up in each ambassador's profile (Phone row, Email row, and the WhatsApp
button uses the optional **WhatsApp** column if present, otherwise falls
back to Contact Number). A GitHub Pages site (or any static hosting) is
public to anyone with the URL — if this ever moves somewhere fully public
and you'd rather not publish contact details, set
`INCLUDE_CONTACT_INFO=false` (as an env var locally, or a repo Variable for
the GitHub Action) and re-sync.

## 7. The "Apply Now" CTA

The band at the bottom of the page ("Want to become an ambassador?") links
to a `mailto:` address by default. Open `index.html`, find the
`cta-band__btn` link near the bottom, and swap the `href` for whatever you
actually want — a Google Form, a Typeform, a real email address, etc.

## Notes on the data files

`data/ambassadors.json` and `js/ambassadors-data.js` are **generated
files** — edit the Google Sheet and re-run the sync (or let the GitHub
Action do it), don't hand-edit these directly.

## Credits

- Map data: [`@svg-maps/india`](https://www.npmjs.com/package/@svg-maps/india) (CC BY 4.0), based on original work by MapSVG.
- Fonts: Montserrat (Open Font License) and DIN Next (as supplied).
- Icons: small original inline SVG set, not traced from any icon library — kept the portal fully self-contained with no font/CDN dependency.
#   a m b a s s a d o r - c o m m u n i t y - p o r t a l  
 