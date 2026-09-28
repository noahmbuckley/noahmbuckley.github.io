# START HERE — Content MODE gold, main set (310 items, blind, 2026-09-28)

**Where:** validation PWA → task **"T1 - Content MODE gold (310, blind)"** (`c26-content-mode-310`).
**Code this AFTER the 40-item reliability round** (`c26-content-mode-rel40`) is done and its Noah-John kappa is known
(`campaign2026/validation/DECISION_RULES_content_mode_v2_2026-09-28.md`: kappa ≥ 0.60 → 9 classes; otherwise the pre-declared 4-class collapse).
The 310 are the rebuilt sample minus the 40: 350 items after dropping programmes, party-less debate turns and moderator/multi-speaker
debate turns, with replacements drawn from the same source × party design (`campaign2026/validation/content_mode_v4_dropped_2026-09-28.csv`).

**Per item:** same as the reliability round: PRIMARY mode (9 modes or `unreadable`), all modes present (tap, at most 2, primary included),
specificity 0-3 (blank for `unreadable`), notes. The codebook v4 at the top of the card is the identical rule text the classifier gets.
Median text is about 800 characters; budget roughly 3 hours in total, split over several sittings; export any time (partial exports load).

**Export:** menu → Export answers → `~/Dropbox/_validation_exports/validation_c26-content-mode-310_<date>.json`, then
`Rscript campaign2026/code/26l2_load_content_mode_v4_gold.R`. Blind predictions are opened only after the codes are written.
**Do not open** `content_mode_v4_predictions_BLIND_2026-09-28.csv` until coding is finished. The sample is stratified on source × party
(and the 40 on predicted mode), not proportional, so pooled accuracy from it is in-sample; see the decision-rules file.
