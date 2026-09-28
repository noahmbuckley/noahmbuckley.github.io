# START HERE — Campaign content MODE gold (350 items, blind, 2026-09-28)

**Where:** validation PWA → task **"Campaign content MODE gold (350, blind)"** (`c26-content-mode-350`).

**What it is:** the 350-message blind gold for `26_content_mode.py` (prompt v2), drawn 2026-09-15 stratified
source × party × predicted mode, order shuffled. Sources: debate turns, TV ads, programmes, party sites, TG, VK,
poster OCR. **No model output is shown or stored in this chunk** (items carry only source, party, region name,
date, text; nothing is highlighted as LLM). Text is the FULL classifier input (up to 3,000 characters), recovered from the classifier's own input tables rather than the workbook's 600-character cut; a "Text length" line under each text says how long it is and flags any item where the full text could not be recovered. 198 of 350 have no region (national
sources) and show "—". 69 have no date.

**Per item (the texts are long, median about 1,000 characters, so about 30-45 s each and roughly 3-4 hours in total, best split over several sittings; stop and export any time, the loader handles partial
exports):**
1. **PRIMARY mode** — tap one of the 9 (keys 1-9 on a Mac). Definitions are on each button and in full at the top
   (verbatim from the workbook codebook).
2. **All modes present** — optional text: ids separated by `|` (e.g. `policy_specific|attack`). Blank = primary only;
   the primary is added automatically. Full ids are safest; unique prefixes work, ambiguous ones (`val`, `eco`) are
   flagged by the loader, not guessed.
3. **Specificity 0-3** — tap.
4. Notes — optional.

**When done / partial:** menu → Export answers → save to `~/Dropbox/_validation_exports/` (file
`validation_c26-content-mode-350_<date>.json`). Then, at the Mac:
`Rscript campaign2026/code/26l_load_content_mode_gold.R`. It writes your codes FIRST to
`campaign2026/validation/c26_content_mode_noah_codes_2026-09-28.csv` (keyed by item_id = msg_id) and only then opens
the blind predictions and prints agreement (also vs John's columns if filled in the workbook or `JOHN_XLSX`).

**Do not open** the `predictions_BLIND_UNTIL_DONE` sheet of the xlsx before you finish. John codes his own copy in
`~/Dropbox/Campaign2026_Shared/`; the iPad chunk and his copy are independent.

**What it feeds / bars:** the proposed (not adopted) decision rules are in
`campaign2026/validation/DECISION_RULES_PROPOSED_2026-09-28.md`.
