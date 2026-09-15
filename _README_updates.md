# Website Updates (Feb 2026)

## Changes Made

### 1. Layout Improvements
- **Wider sidebar**: Increased from ~200px to 260px for better prominence
- **Better centering**: Added 80px left margin to content area for improved balance
- **Responsive**: Layout adjusts appropriately on mobile devices

### 2. SEO Optimization
- Added comprehensive meta descriptions to all pages
- Configured Open Graph and Twitter Card tags for social sharing
- Added structured keywords for search engines
- Enabled sitemap generation
- Added site-url configuration for proper indexing
- Set up Google Analytics placeholder (update with your GA4 ID)

### 3. CV System
- Created markdown-based CV in `../cv/` directory
- Supports multiple output formats:
  - HTML (for web viewing)
  - PDF (for download, matches current CV style)
  - LaTeX (can export if needed)
- Build script (`cv/build_cv.sh`) generates all formats
- Easy to maintain - edit one markdown file, get all formats

## Building the Website

From the `website/` directory:

```bash
quarto render
```

This will regenerate all HTML files in the `docs/` folder.

## Building the CV

From the `cv/` directory:

```bash
./build_cv.sh
```

This creates HTML and PDF versions of the CV.

## Publishing

The site is configured for GitHub Pages. After making changes:

```bash
cd website/
quarto render
cd docs/
git add .
git commit -m "Update website"
git push
```

## Creating Unlisted Pages

To create a page that's not in the sidebar menu:

1. Create a `.qmd` file in the website directory (e.g., `hidden-page.qmd`)
2. Don't add it to `_quarto.yml` sidebar contents
3. The page will be accessible at `/hidden-page.html` but won't appear in navigation

To make it truly hidden from search engines, add to the page YAML:
```yaml
---
title: "Hidden Page"
robots: noindex, nofollow
---
```

## Google Analytics

To enable analytics:
1. Get your Google Analytics 4 (GA4) measurement ID
2. In `_quarto.yml`, replace `"G-XXXXXXXXXX"` with your actual ID

## Sitemap

A sitemap is automatically generated at `docs/sitemap.xml` when you render the site. Submit this to:
- Google Search Console
- Bing Webmaster Tools

## Next Steps

1. Build and preview the updated site
2. If satisfied, commit and push changes
3. Set up Google Analytics (optional)
4. Submit sitemap to search engines
5. Consider adding a `robots.txt` file if needed

---

# Redesign, September 2026

- **Layout**: left sidebar replaced by a top navbar (Research · Teaching · Writing ▾ · CV; Email · Scholar on the right). Design lives in `custom.scss` (warm paper background, Source Serif 4 headings, Inter body, one accent colour). `styles.css` only carries course-card and `hr` rules.
- **Home**: hero (name / role / affiliation) with a commented-out photo slot (`files/noah.jpg`), bio, a "Recent" box, and the contact block. `contact.qmd` and `links.qmd` were retired; old `/contact.html` and `/links.html` URLs now 404.
- **Research**: styled `.pub` entries (title / authors / venue / DOI + inline Abstract toggle), the three older working papers, a **Work in progress** list drafted from `_notes/project_index.md` for Noah to prune (HTML comment in the source), and public writing moved here from the CV.
- **Teaching**: 2026–27 modules first (POU11011 links to its course site), supervision, other Trinity modules, earlier teaching collapsed. Course sites live in `teaching/<code>/` and are published by `~/Dropbox/teaching/templates/slides/publish-site.sh`.
- **Advice pages** (revised 2026-09-15): no nav menu for them. The research guide is linked from Teaching. `ai.qmd` (draft) and `claude-code.qmd` are unlisted (`noindex`) and linked only from `resources/index.html`.
- **Revision 2026-09-15**: navbar = three links on the right, never collapses (`collapse: false`), no search, no Email/Scholar items; navbar aligned to the 700px text column. One typeface (Source Serif 4). Recent box removed. Publications and courses use an `.entry` layout with the year/term in a left gutter.
- **CV**: AJPS paper now published (doi:10.1111/ajps.70060, early view June 2026); Sweden policy-panel talk (Sep 2026) added; teaching list synced. Same edits applied to the canonical `../cv/cv.qmd`; rebuild the PDF with `../cv/build_cv.sh` when convenient.
- `check_updates.py` still reviews index/research/cv only; add `teaching.qmd` and `ai.qmd` if they should be checked nightly.
- **noindex fix (2026-09-15)**: Quarto silently ignores a bare `robots:` front-matter key, so `alternate-russias`, `election-fraud` and `claude-code` never actually carried noindex. Unlisted `.qmd` pages now use `include-in-header` with the meta tag plus `search: false` (keeps their text out of `docs/search.json`). Use that block for any new unlisted page.

# Round 3, 2026-09-15

- **Home**: no h1 or role line (the name appeared twice with the navbar brand); a visually-hidden h1 keeps the page accessible. ORCID (0000-0002-4641-6664, verified) added to "Elsewhere".
- **Resources page** (`resources.qmd`, unlisted draft): Guides (research guide, AI, Claude Code), Data (replication data on Dataverse; a slot for datasets Noah releases; Russian data sources), and the links from the retired `links.qmd` (dead Political Methodologist domain dropped; Cochrane and APSA eJobs URLs corrected). To go live: see the comment at the top of the file.
- **Unlisted area moved** `resources/` → `internal/` so the public page gets `/resources`. `404.html` forwards only known old subpaths (tested 15/15). Producers repointed: `~/Dropbox/teaching/templates/slides/publish-site.sh`, `me/tcd/tutor/web/build_site.py`, `internal/build_apps.sh`.
- **Research**: every paper now carries its verified free version (PDF = publisher copy, Preprint = author version) and Dataverse replication data where it exists (5 of 10). 2014 E-AS title corrected to "…Election and Appointment" (Crossref) and DOI added.

# Round 4, 2026-09-15

- **Unlisted area renamed** `desk-z417xq/` → `internal/` (Noah: easier to remember). Index at https://noahbuckley.me/internal/ (`internal/index.html`). The name is guessable; passphrase anything sensitive.
- **Data page** (`data.qmd`, unlisted draft, linked from `internal/index.html`): replication data on Dataverse, datasets Noah has built (none released yet), Russian data sources.
- **Resources page** now holds only guides and general links; its data sections moved to the Data page.
- **Work in progress** cut to six developed papers (drafted and presented or submitted), titles and coauthors only; no abstracts or descriptions for now.

# Round 5, 2026-09-15

- **Favicon**: lowercase serif "nb" in a site-blue circle (Noah picked it over a bold "NB" square that "looks a bit like a newspaper"). Files: `favicon.ico` (16/32/48, root, requested by default so hand-written pages get it too), `files/favicon.png` (192px, set as `website: favicon`), `apple-touch-icon.png` (180px, root). Drawn with PIL from Georgia Bold so it looks the same everywhere; no live-text SVG.
- **This changelog** renamed `README_updates.md` → `_README_updates.md`: Quarto skips files starting with `_`, so it is no longer published as a public page or listed in the sitemap.
- **Internal index** retitled "Internal" (was "Resources").
- **Course site** (POU11011) title shortened to "POU11011" in its own `_quarto.yml` (teaching folder): the long navbar title made the site scroll sideways on phones and doubled up tab titles.
