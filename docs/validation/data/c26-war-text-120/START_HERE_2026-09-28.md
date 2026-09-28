# START HERE — War-salience pilot TEXT gold (120 items, blind, 2026-09-28)

**Where:** validation PWA → task **"War-salience pilot TEXT gold (120, blind)"** (`c26-war-text-120`).

**What it is:** blind gold for the text codes of the 10-channel governor pilot (`26_` prompt v3: `war_frame`,
`primary_mode`, `military_bio`), the prerequisite for quoting any pilot estimate or approving the scale-up.
120 posts, 24 per predicted war-frame bucket (none / local_security / military_identity / front_support /
war_policy); channel, period and all model output are hidden; text is the classifier input (up to 3,000 characters) rather than the workbook's 1,500-character cut, with a "Text length" line. See
`campaign2026/notes/session_2026-09-27_war_salience_pilot.md`. (The 150-image sheet stays in xlsx.)

**Per item (about 25-40 s each, so roughly 1-1.5 hours):**
1. **War frame(s)** — text: any of `local_security | front_support | military_identity | war_policy` separated by
   `|`; **leave blank if the war is absent**. Definitions at the top (verbatim). WWII memory alone is NOT a frame.
2. **PRIMARY mode** — tap one of the 9 (keys 1-9). An item counts as coded once this is set.
3. **military_bio** — TRUE only if the text frames the AUTHOR's OWN military service/veteran identity.
4. Notes — optional.

**Export / load:** menu → Export answers → `~/Dropbox/_validation_exports/`; then
`Rscript campaign2026/code/26n_load_war_text_gold.R`. Codes go first to
`campaign2026/validation/c26_war_text_noah_codes_2026-09-28.csv` (keyed by item_id = msg_id); then per-frame
precision/recall is computed with stratum weights (`war_pilot_text_bucket_sizes_2026-09-28.csv`; recall from the
raw 24-per-bucket sample is not a population recall).

**Bars (proposed, not adopted):** `campaign2026/validation/DECISION_RULES_PROPOSED_2026-09-28.md`.
