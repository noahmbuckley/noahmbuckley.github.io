# `teaching/` — public pages built outside this Quarto project

Source copies of pages served at `noahbuckley.me/teaching/...`. The site's
`_quarto.yml` lists `teaching/**` as a resource, so a full `quarto render`
copies this folder into `docs/teaching/`. Don't edit files here by hand; each
subfolder is written by its publish script, which also mirrors it into `docs/`.

| Folder | Built by |
|---|---|
| `research-guide/` | `~/Dropbox/teaching/research-supervision/publish-guide.sh` |
| `<code>/` (e.g. `pou11011/`) | `~/Dropbox/teaching/templates/slides/publish-site.sh "<course>"` |

Why the source copy exists: a full site render empties `docs/` first, so
anything only in `docs/` is deleted. Conventions: `../resources/README.md`.
