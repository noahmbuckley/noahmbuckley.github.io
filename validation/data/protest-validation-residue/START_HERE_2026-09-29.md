# START HERE -- Protest data validation: referee residue (2026-09-29)

**Where:** validation PWA -> task **"Protest data validation: referee residue (tasks 1-5)"** (`protest-validation-residue`).
**Not yet in `tasks.json`** (the entry is in the session report); add it and bump `VERSION` in `sw.js` before it appears on the iPad.

**What it is:** the 40 items on which the two silver referees (Claude Opus 5 and gpt-5) disagreed or one said 'unclear', from the protest-data validation package (`eventsData/protestData/validation/pkg_2026-09-28/SUMMARY.md`). Everything both referees agreed on is NOT here. Nothing shown is a model or database label; there is no stratum or verdict on any card.

**Composition:** task 1: 12; task 2: 7; task 3: 2; task 4: 2; task 5: 17. Task 1 = is it a real protest? Task 2 = the same question on articles the production classifier had never labelled. Task 3 = protest date. Task 4 = region. Task 5 = same protest event? (merge / near-miss / self-dedup pairs). The question changes by item and is printed above each text.

**Realistic time:** about 20-30 s per article, about 30 s per pair; 30-40 minutes in one sitting.

**When done / partial:** menu -> Export answers -> save to `~/Dropbox/_validation_exports/` (`validation_protest-validation-residue_<date>.json`).
Then `Rscript eventsData/protestData/code/validation/61_load_residue_answers.R`. It writes your codes FIRST to
`validation/pkg_2026-09-28/results/residue_noah_codes.csv`, and only then opens the referee answers and production labels and prints agreement.

**What it changes:** silver (two-referee agreement) has no human calibration for these tasks. Your answers on the hardest items resolve the
residue, so each headline estimate in SUMMARY.md can be given with the residue counted as your verdict instead of as a bound.
