# START HERE — Campaign message TOPICS gold (150 items, blind, 2026-09-28)

**Where:** validation PWA → task **"Campaign message TOPICS gold (150, blind)"** (`c26-topics-150`).

**What it is:** the 150-post human gold for `25_message_topics.py` (`message_topics.parquet` → `topicshare_*`),
sitting uncoded since 2026-06-27. All posts are from June 2026 (1-21 June), TG/VK party-channel posts; party mix er
47, ldpr 43, kprf 32, np 23, yabloko 5. Text is the FULL classifier input (up to 3,000 characters, read from the same unified TG table `25_` used), not the workbook's 400-character cut; a "Text length" line says how long it is. The source sheet was sorted by party; the
chunk is shuffled once (seed 20260928). No model output is shown or stored.

**Per item (about 20-30 s each, so roughly 1-1.25 hours):**
1. **Political/campaign message?** Yes / No (keys 1, 2). If No the primary topic is set to `other` automatically
   and the other fields are hidden.
2. **PRIMARY topic** — one of 16 (definitions at the top, verbatim from the codebook).
3. **All topics touched** — optional text, ids separated by `|`; blank = primary only. Unique prefixes work;
   ambiguous ones (`eco`) are flagged by the loader.
4. Notes — optional.

**No mode/specificity fields here, on purpose:** the workbook's topics tab has empty mode columns, but the docs
say this tab was folded in only so `25_` gets scored, and there is no model mode prediction for these rows.

**Export / load:** menu → Export answers → `~/Dropbox/_validation_exports/`; then
`Rscript campaign2026/code/26m_load_topics_gold.R`. Codes are written first to
`campaign2026/validation/c26_topics_noah_codes_2026-09-28.csv` (keyed by item_id `c26top_###` with the workbook
row_id), then scored against the blind `topics_150_predictions_BLIND` sheet.

**Bars (proposed, not adopted):** `campaign2026/validation/DECISION_RULES_PROPOSED_2026-09-28.md`.
