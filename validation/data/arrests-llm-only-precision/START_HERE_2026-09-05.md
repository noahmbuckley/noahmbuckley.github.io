# START HERE — Arrests LLM-only precision

**Where:** open the validation PWA on your iPad (same app as the earlier
arrests-sample-A/B/C/D chunks). Pick the task named
**"Arrests LLM-only precision (100)"**.

**What it is:** the 2026-05-07 cross-project LLM audit flagged that nobody had
ever checked the precision of arrests the LLM found that a human never saw —
either because they came from Telegram/Shkulev/Sledcom (sources that were
never hand-coded at all) or because they're FPP events the LLM called an
arrest that the original hand-coded FPP spreadsheet missed. This chunk is 100
such events: 25 each from FPP-LLM-only, Telegram, Shkulev, Sledcom, spread
across crime types within each source.

**Per event you'll see:** the source text (Russian), plus everything the LLM
extracted — official name/position/level, crime_type, arrest_stage,
is_corruption, in_office, region, whether it's flagged as a federal event.

**What to record per item:**
- `is_real_corruption_arrest_of_official` — **Yes / No / Unsure.** Is this
  actually a corruption/legal-case arrest OF AN OFFICIAL — not a random crime
  report, a rumor, someone merely mentioned in passing, or a private citizen?
  This is the main precision question.
- `type_correct` — is the LLM's `crime_type` roughly right? Yes/No/Unsure.
- `region_correct` — is the region roughly right? Yes/No/Unsure.
- `notes` — free text, especially for anything weird (multi-defendant case
  collapsed into one row, official actually a private citizen, etc — these
  feed the separate multi-defendant-collapse issue in CLAUDE.md too, worth a
  note if you spot one).

**When done:** tap Export. Save the file
(`validation_arrests-llm-only-precision_<date>.json`) to
`~/Dropbox/_validation_exports/` — the same folder every other arrests/disaster
export goes to.

**What this feeds:** an honest precision estimate (with a 95% Wilson CI) for
the 8,652 FPP-LLM-only arrests plus the three never-hand-coded sources,
answering the 2026-05-07 audit's open item 3 ("no precision check on the
LLM-only arrests"). Overall and per-source precision numbers are what decide
whether these sources can be trusted as-is in the arrests paper, or need a
stricter LLM re-classification pass first.

**Loader (run after you export):**
```
Rscript eventsData/code/99d_load_llm_only_precision_results.R
```
Writes `eventsData/output/validation_llm_only_precision_handcoded.csv` and
prints precision overall, by source, and the type/region-correct rates, each
with a Wilson 95% CI.
