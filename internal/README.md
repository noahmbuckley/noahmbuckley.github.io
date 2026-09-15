# `internal/` — unlisted pages on noahbuckley.me

**Moved from `resources/` on 2026-09-15** so the public Resources page can have
`/resources`. Renamed `internal/` the same day (easy to remember). Bookmark https://noahbuckley.me/internal/.
**The name is guessable**, so anything that needs real protection gets a passphrase (see below).
Old `/resources/<page>` and `/private/<page>` links to the pages listed below are
forwarded by `404.html`; `/resources/` itself now goes to the public Resources page.

Renamed from `private/` on 2026-09-11 (the old name read badly in URLs). Old
`/private/...` links still work: the site's `404.html` forwards any
`/private/<path>` to `/internal/<path>`, keeping `#anchors`, and
`/private/teaching/research-guide/` to the now-public `/teaching/research-guide/`.

Pages here are **unlisted, not secret**:

- Nothing on the public site links to them; you reach them from the index,
  https://noahbuckley.me/internal/ (`index.html` in this folder). **Add every
  new for-me page there.**
- Every page carries `<meta name="robots" content="noindex, nofollow">`.
  `robots.txt` deliberately does NOT `Disallow: /internal/`: a robots block
  stops crawlers reading the noindex tag, so a URL that leaks via a link can
  still be listed bare. noindex alone is the stronger signal.
- The repo is PUBLIC, so anyone browsing GitHub can see `docs/internal/`.
  Treat obscurity as a courtesy, not a control. Nothing with personal data,
  student data, or unpublished results that matter goes here.

## The one rule: build into the source tree, never into `docs/` alone

A full `quarto render` of the site (the nightly `_update/run_updates.sh`
does one) **empties `docs/` and rebuilds it** from the source tree. Anything
that exists only in `docs/` is deleted. This happened to the teaching pages
on 2026-09-11 (caught before any push).

So every page built outside the Quarto project lives in a source folder that
`_quarto.yml` lists under `resources:`, and the render copies it into `docs/`:

| Source folder | Served at | Listed as |
|---|---|---|
| `internal/` | `/internal/...` (unlisted) | `internal/**` |
| `teaching/` | `/teaching/...` (public: research guide, course sites) | `teaching/**` |
| `validation/` | `/validation/...` | `validation/**` |

Publish scripts write the source folder first and then mirror it into
`docs/` (so no render is needed to go live). Both copies are committed.

## Passphrase protection

**Teaching decks** (`teaching/<code>/slides/`): encrypted by
`~/Dropbox/teaching/templates/slides/publish-site.sh <course> --encrypt "..."`,
which encrypts the *source* copy, so renders keep the encrypted version. The
passphrase is recorded in `~/Dropbox/teaching/README.md` (NOT here: this repo
is public).

**Other pages**: `../encrypt_page.sh` wraps StatiCrypt (client-side AES via
`npx staticrypt`):

```bash
cd ~/Dropbox/Projects/me/website
./encrypt_page.sh internal/apps/sdb/edit/index.html "silly phrase"
git add docs/internal/apps/sdb/edit && git commit -m "encrypt" && git push
```

It encrypts only the `docs/` copy and leaves the source plain, so **a full
site render undoes it**: re-run after every full render. The encrypted HTML
is public, so a short passphrase is brute-forceable offline; fine for "purely
for me" convenience pages, not for anything sensitive.

**Decision 2026-09-03: none encrypted for now** (other than the teaching
decks). Candidates if that changes: `apps/sdb/edit/`, `apps/tracker/edit/`,
`sdb_report/`. `tutor-desk/` stays open — it is meant to be shared with
colleagues.

## If obscurity stops being enough

noahbuckley.me is already fronted by Cloudflare, so **Cloudflare Access**
(free ≤50 users, one-time email code, can allowlist `@tcd.ie`) is a
configuration step, not a migration. Prefer that over per-page passphrases
once more than a couple of pages need real access control.

## Pages

| Path | What | Source of truth |
|---|---|---|
| `index.html` | index of everything below | hand-edited (publish-site.sh adds deck lines) |
| `tutor-desk/` | College Tutor reference (TCD) | `me/tcd/tutor/web/build_site.py` writes it |
| `apps/sdb/`, `apps/sdb/edit/` | FRG app | `build_apps.sh` |
| `apps/tracker/`, `apps/tracker/edit/` | Tracker app | `build_apps.sh` |
| `viewer/` | viewer | `build_apps.sh` |
| `sdb_report/` | SDB report | sdb project |
| `talks/` | slide decks | Quarto revealjs (see `disaster/slides/README.md`) |
| `teaching/<code>/slides/` | Noah's complete lecturing decks (encrypted) | `~/Dropbox/teaching/templates/slides/publish-site.sh` |
| `bike-computer/` | DIY e-ink bike computer intro | sanitised copy of `me/bikeComputer/artifact/bike_computer_feasibility.html` (regenerate from there; never hand-edit) |

The public course pages (`/teaching/<code>/`) and the research guide
(`/teaching/research-guide/`, public since 2026-09-11, rebuilt by
`~/Dropbox/teaching/research-supervision/publish-guide.sh`) live in the
top-level `teaching/` folder, not here.
