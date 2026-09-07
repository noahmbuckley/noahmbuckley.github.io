# `private/` — unlisted pages on noahbuckley.me

Pages here are **unlisted, not secret**. The convention, decided 2026-09-03:

- Nothing links to them from the public site; you reach them from
  `resources.html` (https://noahbuckley.me/private/resources.html), the
  central index. **Add every new for-me page there.**
- Every page carries `<meta name="robots" content="noindex, nofollow">`.
  `robots.txt` deliberately does NOT `Disallow: /private/` any more: a robots
  block stops crawlers reading the noindex tag, so a URL that leaks via a link
  can still be listed bare. noindex alone is the stronger signal.
- The repo is PUBLIC, so anyone browsing GitHub can see `docs/private/`.
  Treat obscurity as a courtesy, not a control. Nothing with personal data,
  student data, or unpublished results that matter goes here.

## Passphrase protection (available, unused)

`../encrypt_page.sh` wraps StatiCrypt (client-side AES via `npx staticrypt`):

```bash
cd ~/Dropbox/Projects/me/website
./encrypt_page.sh private/apps/sdb/edit/index.html "silly phrase"
git add docs/private/apps/sdb/edit && git commit -m "encrypt" && git push
```

It encrypts only the `docs/` copy; the source under `private/` stays plain,
so rebuilds keep working — **re-run after every rebuild of that page**. The
encrypted HTML is public, so a short passphrase is brute-forceable offline;
fine for "purely for me" convenience pages, not for anything sensitive.

**Decision 2026-09-03: none encrypted for now.** Candidates if that changes:
`apps/sdb/edit/`, `apps/tracker/edit/`, `sdb_report/`. `tutor-desk/` stays
open — it is meant to be shared with colleagues.

## If obscurity stops being enough

noahbuckley.me is already fronted by Cloudflare, so **Cloudflare Access**
(free ≤50 users, one-time email code, can allowlist `@tcd.ie`) is a
configuration step, not a migration. Prefer that over per-page passphrases
once more than a couple of pages need real access control.

## Pages

| Path | What | Source of truth |
|---|---|---|
| `resources.html` | index of everything below | hand-edited |
| `tutor-desk/` | College Tutor reference (TCD) | `me/tcd/tutor/web/build_site.py` writes it |
| `apps/sdb/`, `apps/sdb/edit/` | FRG app | `build_apps.sh` |
| `apps/tracker/`, `apps/tracker/edit/` | Tracker app | `build_apps.sh` |
| `viewer/` | viewer | `build_apps.sh` |
| `sdb_report/` | SDB report | sdb project |
| `talks/` | slide decks | Quarto revealjs |
| `teaching/research-guide/` | "Doing political science research" advice page (capstone + MSc) | `~/Dropbox/teaching/research-supervision/guide/` — `quarto render`, then copy `output-guide/` here |


## Teaching decks (2026-09-03)

`docs/private/teaching/<code>/slides/` — Noah's complete lecturing decks, pushed by `~/Dropbox/teaching/templates/slides/publish-site.sh <course> --encrypt "passphrase"`. The passphrase is recorded in `~/Dropbox/teaching/README.md` (NOT here: this repo is public). Public course pages sit at `docs/teaching/<code>/`. Linked from resources.html.

## Research guide (2026-09-07)

`docs/private/teaching/research-guide/` — the cross-course "how to do research" advice page for
capstone and MSc students. **Unlisted while it is still a draft**: it carries four visible
"Note to Noah" boxes (`.cc`) and a couple of `[TBD]`s that only Noah can fill. Rebuild with
`cd ~/Dropbox/teaching/research-supervision/guide && quarto render`, then
`rsync -a --delete --exclude sitemap.xml --exclude robots.txt ../output-guide/ ~/Dropbox/Projects/me/website/docs/private/teaching/research-guide/`.
When it is ready for students it moves to the public `docs/teaching/research-guide/`
(the URL the capstone syllabus, index and emails already cite) — and the `.cc` boxes must be
hidden first (`display: none` on `.cc` in the guide's `styles.css`).
