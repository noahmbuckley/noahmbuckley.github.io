# START HERE -- FPP primary_type gold (170, v2, 2026-09-09)

**Where:** open the validation PWA (same app as the arrests/disaster chunks). Pick the task named **"FPP primary_type gold (170, v2)"**.

**What changed from v1:** v1 (150 items) showed the SAME 9-way typology menu to every item regardless of why it was sampled. v2 fixes four things Noah flagged: (1) the two boundary strata now ask a factual binary question instead of a 9-way menu; (2) that binary question no longer states our decision rule, so your answer is an independent check on the rule rather than an application of it; (3) ~12% of items are silent repeats so we can measure your own test-retest agreement; (4) the truncated `region` field ("Вологодс" etc.) is fixed. v1's file is kept at `items_v1.json.bak` for reference, not loaded by the app.

**Two question types, by stratum (you are not told which stratum an item is from):**

- **BINARY** (131 items -- strata A "contested arrest/removal" + B "governor_political"): "Does the text state a crime, criminal case, investigation, court action, or formal charge against this person?" -- Yes / No / Unclear. This is a factual reading question, not a category choice -- read only what the text says. Estimated ~5 seconds/item.
- **TYPOLOGY** (39 items -- stratum C, random control): the full 9-way `primary_type` choice + Ambiguous, same as v1, with the v2 category definitions (including the arrest_legal/governor_political rule) shown above every item. Estimated ~20 seconds/item.

**Realistic total completion time: about 24 minutes** (131 x 5s + 39 x 20s = 1435s = 23.9 min of pure answering time). Expect somewhat more in practice for reading, occasional notes, and breaks -- budget 25-35 minutes if doing it in one sitting.

**Repeats are SILENT.** ~12% of the 170 items (20 of them) are exact repeats of an earlier item in this same list, shown again later at an unpredictable position. You are not told which ones. Just answer each item as it comes -- the loader compares your two answers on each repeated event afterward to measure your own test-retest agreement, which is the only way to tell how much of any model's "error" is actually just labelling noise.

**What to record per item:**
- BINARY items: `legal_predicate_stated_gold` (Yes/No/Unclear) + optional Notes.
- TYPOLOGY items: `primary_type_gold` (pick ONE of the 9 categories or Ambiguous) + Notes (please say why if Ambiguous).

**When done:** tap Export. Save the file (`validation_fpp-primary-type-gold_<date>.json`) to `~/Dropbox/_validation_exports/` -- the same folder every other export goes to.

**What this feeds:** `eventsData/code/99e_load_primary_type_gold_results.R` scores all 4 model arms (Haiku-v1, Haiku-v2, nano-low-v1, nano-low-v2) against your labels -- per-stratum accuracy, a population-reweighted overall accuracy (using the TRUE stratum base rates in the full production cache, not the oversampled rates in this chunk), and your own test-retest agreement from the 20 repeats.

**Status as of the build date:** this chunk is BUILT AND REGISTERED but the website has NOT been redeployed (no `quarto render`, no push) -- deployment is a separate, later step.

