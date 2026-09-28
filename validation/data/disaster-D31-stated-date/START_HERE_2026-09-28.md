# START HERE — Disaster D-31 stated-date validation (v2, rebuilt 2026-09-28)

**Supersedes** `START_HERE_2026-09-05.md` (old 60-item chunk: `items_2026-09-05.json.bak`).
Same task in the app: **"Disaster D-31 — stated-date validation (75)"**.

## What it checks
The stage-09 LLM read matched media/social text and extracted a `stated_event_date`. For 1,756
events that date is the day used in the DiD (`best_date_source == llm_stated_date`). Nobody has
checked it against reality. Per item: is the stated date the **day the accident/disaster itself
happened**?

## What is new in v2: the "later-event date" stratum (audit D-57)
Some FPP entries are about the legal/aftermath step (Krymsk eventid 7932: "start of hearings").
The concern: the extractor (or the pipeline) picks a **trial / court / anniversary / aftermath
date** instead of the event date. Items are tagged with why they were sampled ("Why sampled"):

| tier | rule | pool | shown |
|---|---|---:|---:|
| W | stated date > 45 d outside the FPP month; the pipeline's ±45 d window rejects it (NOT in the DiD). Includes Krymsk 7932 | 7 | 7 |
| T | суд / судебн / приговор / обвинительн / годовщин / слушани / апелляц / "лет назад" in FPP text, date quote or LLM summary | 9 | 9 |
| O1 | stated date after the last day of the FPP month | 18 | 10 |
| O2 | stated date > 7 d before the FPP month | 30 | 6 |
| M | extractor confidence = medium (none of the above) | 42 | 8 |
| H | high-confidence random baseline, spread across years | 1,657 | 35 |

(pool = 1,756 llm_stated_date events + W; strata mutually exclusive, priority W>T>O1>O2>M>H.)

**Finding to know before you start:** in Krymsk 7932 the extractor's stated date (2012-07-06) is
the CORRECT flood date; the FPP month (2013-05) is the trial month. The pipeline's ±45 d window
rejected the extractor's date and the dossier fell back to `media_first` (2013-04-22). So D-57's
"trial date mistaken for the event" was a window/FPP-month problem, not an extractor error, in
that case. Stratum W tests whether that is typical (7 events only exist).

## Per item — what to record
- `true_date` — the real EVENT date (YYYY-MM-DD; partial ok). Fill it whenever you find it, especially for NO.
- `matches_event` — **Yes = stated date is the exact event day** (first day for multi-day events); No; Unsure.
- if No: `error_type` — trial/court/aftermath/anniversary; earlier or other date; publication date; different incident; same event off by a few days.
- `notes`.

## DECISION RULE (pre-declared 2026-09-28, before any coding)
> **PROPOSED BY CC — NOT PREVIOUSLY DEFINED; Noah to confirm or edit BEFORE coding.**
> The existing docs (`audit_2026-05-13.md:220`, the 09-05 START_HERE) say only "drop sources
> below ~70% accuracy" and never define how close a date must be. There is no tolerance N.

1. **"Correct" = `matches_event == yes` = exact event day** (N = 0). Secondary statistic:
   agreement within **±3 days**, computed by the loader from `true_date` (±3 matters for the 7-
   and 14-day treatment windows).
2. **Statistic** = post-stratified accuracy over the 1,756-event pool (strata T, O1, O2, M, H
   weighted by pool size; W excluded and reported separately; 'unsure' excluded and its count
   reported). The oversampled suspicious strata do NOT drive the headline.
3. **Rule:** point estimate **< 70%** → `llm_stated_date` is not trusted at day precision until fixed
   (Noah decides the fix; nothing automatic). 95% CI straddling 70% → reported as **inconclusive**,
   not as a pass.
4. Per-stratum accuracy and the error_type tally are reported as descriptives, not as tests.

**Flag — the result is very sensitive to N.** A separate known-answer check (extractor vs EM-DAT /
Sledcom days, n=101, `disaster/code/validation/99g_known_answer_stated_date.R`) finds exact-day
agreement 42.6% (Wilson CI 33-52), within ±3 d 61%, within ±7 d 71% — those reference dates carry their own
error, so this is not a substitute for your hand check, but exact-day vs ±3 vs ±7 would move
the pass/fail line. Decide N first.

## Export and load
Menu → Export → save to `~/Dropbox/_validation_exports/`. Then
`Rscript disaster/code/validation/99d_load_date_validation_results.R` (writes
`disaster/data/processed/verification/validation_D31_stated_date_handcoded.csv` and prints the
per-stratum table, the post-stratified estimate, and the error tally).
