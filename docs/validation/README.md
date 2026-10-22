# validation — research data hand-validation web app

A small offline-capable web app for hand-coding validation tasks across Noah's
research projects. Lives in the Quarto website so it deploys to
**`https://noahbuckley.me/validation/`** alongside the rest of the site.

## What it does

- Pick a task from a list (each task is a stratified sample to verify)
- Compact card view shows the LLM-coded values highlighted in yellow
- Verdict + override fields with keyboard shortcuts (1/2/3/4)
- Progress saved locally per-task; back/forward through items
- Export answers as JSON; import back into the source project via an R script
- Works **offline** once the page has been opened online once

Designed to work on the **iPad mini** (PWA, "Add to Home Screen") and on the
**Mac** (Chrome / Safari, browser tab) with the same code.

## File layout

```
validation/
├── index.html                         entry point
├── app.js                             all UI + state + IndexedDB logic
├── style.css                          dark-mode aware, iPad-friendly
├── sw.js                              service worker (offline shell + data)
├── manifest.webmanifest                PWA manifest
├── icon-{180,192,512,512-maskable}.png app icons
├── tasks.json                          registry of all validation tasks
└── data/
    └── <task-id>/
        ├── schema.json                 field definitions for one task
        └── items.json                  the items to hand-validate
```

## Currently wired tasks

The live list is `tasks.json`. The program-wide queue that says what each task unblocks, its decision
rule and its loader is `~/Dropbox/Projects/_notes/human_queue_and_paid_runs.md` §1. As of 2026-09-28 the
app carries only Tier-1 tasks: `disaster-D31-stated-date`, `disaster-response-markers`,
`c26-content-mode-350`, `c26-topics-150`, `c26-war-text-120`. Retired entries are kept in
`tasks_retired_<date>.json`, with their `data/` dirs left on disk.

**When tasks change:**
- Bump `const VERSION` in `sw.js` so iPads drop cached items.
- `rsync -a validation/ docs/validation/`.
- Commit only `validation/` + `docs/validation/` in the website repo, then push.

## Adding a new task

1. **Build the items file** — generate a JSON array of items in your project (see `disaster/code/99b_export_for_validation_app.R` for an example).
2. **Create `data/<task-id>/schema.json`** — define `display`, `validation`, `id_field`, optional `instructions`, optional `row_class_field` / `row_class_map`.
3. **Add an entry to `tasks.json`** with `id`, `name`, `description`, `schema_url`, `items_url`.
4. **Write a "load back" R script** in your project that reads the exported JSON and merges answers onto the source data.
5. Re-render the Quarto site (`quarto render`) and push.

### Schema fields supported

**`display`** — one entry per field shown read-only on the card:
- `field` (required) — column name in items.json
- `label` — human label
- `format` — `"compact"` (monospace), `"longtext"` (large wrapped block), `"tone"` (chip), `"link"` (tappable http(s) link),
  `"image"` (the item value is an image path **relative to the directory of the task's `items_url`**, e.g. `img/T2_004.jpg`
  -> `data/<task>/img/T2_004.jpg`; shown full card width, alt text = item id, tap/click opens a full-screen zoom view
  (pinch-zoom natively; tap, Esc, Enter or Space closes). The next 3 cards' images are prefetched.)
- `highlight` — `"llm"` highlights this field as classifier output (yellow background)

**`validation`** — one entry per field the user fills in:
- `field`, `label`, `required`
- `type`: `"enum"` | `"text"` | `"integer"` | `"number"` | `"textarea"`
- `options` (for enum): `[{value, label, key, tone}]` where `key` is the keyboard shortcut and `tone` ∈ `good|bad|warn|neutral`
- `placeholder`
- `key` on enum options: any single character (digit or letter, case-insensitive) is a keyboard shortcut. Fields are scanned
  in schema order and only visible fields count, so avoid reusing a key across fields. `N` is reserved for notes (used only if
  no option claims it). Options without a `key` are tap/click only. The help line under the card is built from the schema.
- `show_if`: `{verdict: ["NO", "BORDERLINE"]}` → only visible when verdict is one of those values

## Usage — Mac (browser tab)

**Desk mode (2026-10-22) — for tasks that need web lookups (elites spot checks, mayor gate, anything
with an evidence link).** Every card gets a `Lookup` chip row: its `format: "link"` fields plus prefilled
searches (Google / Yandex / ru.wiki on the card's `name`; set `"desk": true` on the tasks.json entry or the
schema, or give the schema its own `lookups: [{label, url}]` with `{field}` placeholders). Keys `O` (first
evidence link), `⇧O` (second), `S` (first search) all load into ONE named side window, so after the first
pop-up (allow it for noahbuckley.me) the app sits on the left and the evidence refreshes on the right.
Menu → **Desk mode** auto-opens each card's first evidence link as you advance. Tasks flagged `desk`
show 🖥 in the picker: do those on the Mac, not the iPad.


1. Open `https://noahbuckley.me/validation/` (or for local testing, see below).
2. Tap a task. Items load. Fill in verdicts and notes.
3. Keys: `1`/`2`/`3`/`4` set verdict; `←`/`→` navigate; `Enter` saves & next; `N` jumps focus to notes.
4. When done (or whenever), open the menu (⋮) → **Export answers** → file downloads to `~/Downloads/`.
5. In R, run `disaster/code/99c_load_validation_results.R` (it picks up the most recent export by default), then run the existing `99_process_verification.R`.

### Local testing

Service workers require HTTPS or localhost, so file:// won't work. From this
directory's parent (`me/website/`), run:

```bash
python3 -m http.server 8765
# then open http://localhost:8765/validation/
```

In Chrome: DevTools → Application tab → Service Workers (verify registration);
Application → Storage → IndexedDB → `validation` (verify answers persisting).

## Usage — iPad mini (offline-capable PWA)

**One-time install:**

1. On Wi-Fi, open `https://noahbuckley.me/validation/` in Safari.
2. Tap a task once and let the items load (this caches everything).
3. Tap the menu (⋮) → **Request persistent storage** → confirm if prompted.
4. Tap the share icon in Safari's bottom toolbar → **Add to Home Screen**.
5. From the Home Screen icon ("Validate"), open the app once more on Wi-Fi to confirm it loads as a standalone app.

**Going offline (e.g., airplane):**

- Open the icon. Items, current progress, and prior answers all load from local storage.
- Validate as normal. Everything saves to IndexedDB.
- When back online, the app auto-syncs nothing automatic by design — to get answers back to your project: menu → **Export answers** → share sheet → save to **Files / Dropbox**.

**Reliability rule:** open the icon at least every ~2-3 weeks even briefly. iPadOS will eventually evict storage on long-idle PWAs. The "Sync now" menu item re-pulls everything from the server in one tap if anything has been evicted.

## Round-trip flow (per task)

```
[Project R script] ──build──▶ data/<task-id>/items.json
       └─ committed to git, deployed by Quarto

       Web app reads items.json
              │
              ├─ hand-coding (Noah) ─▶ IndexedDB
              │
              └─ Export ─▶ JSON file

[Project R script] ◀──load── validation_<task-id>_<date>.json
       └─ merges answers onto verification CSV
       └─ existing 99_process_verification.R takes over from here
```

## Known limitations / TODO

- **Region names truncated** in the disaster task — source crosswalk
  `regionid_tomergein.xlsx` truncates the English `region` column to
  ~12 chars ("Komi Republi", "Volgograd ob"). regionid is shown next to it
  so disambiguation is fine, but a fuller English-name lookup would be nicer.
- **Image tasks (added 2026-10-06, drafted, not yet published/exercised by a live task).** `format: "image"` is
  implemented in `app.js`. Offline: `sw.js` serves `data/<task>/img/*` cache-first from a separate **unversioned** cache
  `images-v1` (so a `VERSION` bump does not drop ~40 MB of images), filled on first view or by menu -> **Download task
  images for offline** (progress shown; re-tap retries failures). Wiping images: clear site data (or delete `images-v1`
  in DevTools -> Application -> Cache Storage). If an image is re-rendered, give it a new filename (cache-first never revalidates).
- **No multi-device sync.** Answers live in IndexedDB on one device. If you want to validate from both Mac and iPad, export from one and resume from the other (we can add a server-backed sync layer later if this becomes painful).
- **Export filename** uses today's date, so re-exporting the same day overwrites the previous export. Pick the most recent and import. (R script picks newest by mtime by default.)

## Adding a new task — quick recipe

```r
# example: in <project>/code/99b_export_for_validation_app.R
library(jsonlite)
items <- ...  # data.frame with id_field and display fields
out_dir <- "~/Dropbox/Projects/me/website/validation/data/<your-task-id>"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
writeLines(toJSON(items, dataframe = "rows", null = "null", na = "null",
                  auto_unbox = TRUE, pretty = TRUE),
           file.path(out_dir, "items.json"), useBytes = TRUE)
```

Then add a `schema.json` next to it (copy `disaster-spot-check/schema.json`
and edit the field list), and append an entry to `tasks.json`.
