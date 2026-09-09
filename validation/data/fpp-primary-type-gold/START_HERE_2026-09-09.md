# START HERE -- FPP primary_type gold (67, v3, 2026-09-09)

**Where:** open the validation PWA (same app as the arrests/disaster chunks). Pick the task named **"FPP primary_type gold (67, v3)"**.

**What changed from v2:** v2 (170 items) showed the full 9-way typology menu to a random-control stratum and a factual binary question to two boundary strata. Noah's call this session: shrink to 60 items total, ALL of them boundary items, split into two halves that answer two different questions about the program's silver reference (two independent frontier-model referees, Opus 5 + gpt-5, whose AGREEMENT defines "silver" -- see notes/silver_reference_2026-09-09.md):

- **Half 1 -- referee disagreement (30 items).** The two referees disagree on primary_type for 59/600 events in the validation sample (9.8%). This half draws 30 of those 59 -- specifically the 46 where at least one referee said arrest_legal or governor_political, i.e. where the disagreement plausibly bears on the SAME boundary this whole chunk targets -- sampled proportionally to each item's original stratum. Your answer tells us, per item, which referee (if either) was reading the text the way you do.
- **Half 2 -- silver AGREES but might be wrong (30 items), covering BOTH error directions:**
  - **15 possible FALSE POSITIVES** -- silver says arrest_legal, but the event's own extracted arrest_stage is a bare removal/resignation (removal_from_office / resignation_under_pressure), and/or the current haiku_v2 or nano_low_v2 model dissents from silver's call. If you say "No" on these, that's evidence silver over-called arrest_legal.
  - **15 possible FALSE NEGATIVES** -- silver says governor_political, but haiku_v2, nano_low_v1, or nano_low_v2 says arrest_legal, and/or the text itself contains a legal-predicate cue word (уголовн, дело, следствие, суд, обвин, взятка, задержан, арест, проверка, хищение). If you say "Yes" on these, that's evidence silver under-called arrest_legal (missed a real legal predicate).

**Every item asks the SAME question** (no more typology menu): "Does the text state a crime, criminal case, investigation, court action, or formal charge against this person?" -- Yes / No / Unclear. The 2026-09-09 decision rule is NOT shown, so your answer is an independent check on it, not an application of it. Estimated **~5 seconds/item**.

**Realistic total completion time: about 6 minutes** (67 items x 5s = 335s pure answering time). Expect more in practice for reading and notes -- budget 10-15 minutes in one sitting.

**Repeats are SILENT.** 7 of the 67 items (~10%) are exact repeats of an earlier item in this same list, shown again later at an unpredictable (non-adjacent) position. You are not told which ones. Just answer each item as it comes -- the loader compares your two answers on each repeated event afterward to measure your own test-retest agreement.

**What to record per item:** `legal_predicate_stated_gold` (Yes/No/Unclear) + optional Notes.

**When done:** tap Export. Save the file (`validation_fpp-primary-type-gold_<date>.json`) to `~/Dropbox/_validation_exports/` -- the same folder every other export goes to.

**What this feeds:** `eventsData/code/99f_load_primary_type_gold60_results.R` scores, SEPARATELY (never pooled into one corpus-level number -- this sample is deliberately boundary-only and non-representative): (a) per-referee agreement on the disagreement half; (b) the false-positive confirmation rate and the false-negative confirmation rate, kept apart because a silver error in one direction means something different from the other; (c) every model arm (haiku_v1/v2, nano_low_v1/v2) vs your labels; (d) your own test-retest agreement from the repeats.

**v2 (170 items, two question types) is preserved** at `items_170.json.bak`/`schema_170.json.bak` for reference, not loaded by the app.

**Status as of the build date:** this chunk is BUILT AND REGISTERED but the website has NOT been redeployed (no `quarto render`, no push) -- deployment is a separate, later step.

