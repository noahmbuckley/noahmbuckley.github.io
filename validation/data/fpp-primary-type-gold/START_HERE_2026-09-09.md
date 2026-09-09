# START HERE -- FPP primary_type gold (150)

**Where:** open the validation PWA (same app as the arrests/disaster chunks). Pick the task named **"FPP primary_type gold (150)"**.

**What it is:** the FIRST human gold labels this program has ever had for FPP event `primary_type`. Every number produced so far -- the 2026-09-09 prompt audit, the Haiku-v1 vs nano disagreement, Haiku's self-agreement check, the v2 prompt test -- measures agreement BETWEEN models or prompts, never accuracy against a human reading of the actual text. This chunk closes that gap.

**Blind by design:** you will NOT see any model's prediction for these events -- only the raw Russian text plus year/region. This is deliberate (same convention as the rusSocial blame- attribution gold chunk) so your label isn't anchored by what Haiku or nano guessed.

**150 events, stratified the SAME way as the n=600 model-comparison sample this session also built:** 65 from the contested region (events Haiku-v1 called `arrest_legal` with stage `removal_from_office`/`resignation_under_pressure` -- the exact boundary the 2026-09-09 audit found broken), 50 from `governor_political`, 35 a random control block. You are not told which stratum an item came from.

**What to record per item:**
- `primary_type_gold` -- pick ONE of the 9 categories (definitions are shown above every item, under the persistent instructions banner) or **Ambiguous** if genuinely torn.
- `notes` -- free text; please say why if you pick Ambiguous, and flag anything that doesn't fit the scheme at all.

**Read this before starting:** a forced resignation or removal with NO stated crime/ investigation/court action is `governor_political`, not `arrest_legal` -- per Noah's 2026-09-09 decision, `arrest_legal` requires the text to state a legal/investigative predicate DIRECTED AT the person (a named crime, an opened case, a court action, formal charges, or an oversight-body finding). Bare "отставка"/"увольнение"/"отстранение" with no such predicate is political, not legal, even though the person is leaving office.

**When done:** tap Export. Save the file (`validation_fpp-primary-type-gold_<date>.json`) to `~/Dropbox/_validation_exports/` -- the same folder every other export goes to.

**What this feeds:** `eventsData/code/99e_load_primary_type_gold_results.R` scores all 4 model arms from the 2026-09-09 v2 validation run (Haiku-v1, Haiku-v2, nano-low-v1, nano-low-v2) against your labels -- the first honest ACCURACY numbers (not just agreement) for this classifier, overall and by stratum.

**Status as of the build date:** this chunk is BUILT AND REGISTERED but the website has NOT been redeployed (no `quarto render`, no push) -- per the task instructions for this session, deployment is a separate, later step.

