# START HERE — Content MODE reliability round (40 items, blind, redrawn 2026-09-30)

**Where:** validation PWA → task **"T1 - Content MODE reliability (40, blind, Noah+John)"** (`c26-content-mode-rel40`).
**Replaces** `c26-content-mode-350` (retired: two instrument problems and 61 out-of-scope items found in round 1).

**What it is.** The same 40 messages are coded independently by Noah (this app, or the Excel twin `content_mode_v4_NOAH_twin_2026-09-30.xlsx`) and John (his Excel
copy `FOR_JOHN_content_mode_rel40_v4_2026-09-30.xlsx`), **before** the other 310. The outcome is a human Cohen's kappa on
primary mode (9 classes, `unreadable` excluded). Pre-declared in `campaign2026/validation/DECISION_RULES_content_mode_v2_2026-09-28.md`:
kappa ≥ 0.60 keeps the 9-class measure; kappa < 0.60 switches all scoring to the 4-class collapse.
The 40 are balanced over predicted mode × source (a rare-class-friendly draw, not proportional), shuffled, blind: no model output is
shown or stored in the chunk. **Redrawn 2026-09-30 (decision AUDIT0929-D3 = c):** the 6 items Noah coded on 09-28 under the OLD v3 definitions were moved to the
310 task and replaced by 6 fresh items (same predicted mode × source cells, seed 20260930), because the v4 rules were written from
them. None of these 40 has been coded by anyone before; the kappa rule uses all 40. The 09-28 version of this task and the 09-28
workbooks are superseded: do not code them.

**Per item (about 30-45 s; 25-30 minutes in total):**
1. **PRIMARY mode.** Tap one of the 9 (keys 1-9 on a Mac) or `unreadable` (garbled ASR transcript / fragment you cannot code; use
   sparingly, and leave specificity blank).
2. **All modes present.** Tap-to-select; at most 2, the primary included; blank = primary only.
3. **Specificity 0-3.**
4. Notes (optional).

**Codebook v4** is the text at the top of the card (tap to expand); it is the identical rule text the classifier gets. Also in
`campaign2026/validation/codebook_content_mode_v4_2026-09-28.md`. New in v4: mode vs topic; primary = largest share of substantive
content; party activity reports; party-as-provider association; vague vision + call to vote → values_ideas; `unreadable`.

**Export:** menu → Export answers → save to `~/Dropbox/_validation_exports/` (`validation_c26-content-mode-rel40_<date>.json`). Then
`Rscript campaign2026/code/26l2_load_content_mode_v4_gold.R` (writes the codes FIRST, opens blind predictions only afterwards).
**Do not open** `content_mode_v4_predictions_BLIND_2026-09-30.csv` (or the 09-28 one) or the debate-screen table before you finish.
