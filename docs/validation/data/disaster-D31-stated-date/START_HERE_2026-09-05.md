# START HERE — Disaster D-31 stated-date validation

**Where:** open the validation PWA on your iPad (same app/home-screen icon you
already use for the disaster-sample-E / disaster-date-coding chunks — it lives
at the `me/website/validation/` site). Pick the task named
**"Disaster D-31 — stated-date validation (~60)"** from the task list.

**What it is:** 60 disaster events where the pipeline already extracted a
specific date (`stated_date`) from media text and marked it `day_high`
confidence — but nobody has ever checked whether that date is actually
correct. This is different from the earlier "date-coding" chunk, which filled
in missing days; this one checks dates that already look filled in.

**Per event you'll see:**
- The FPP one-line description (RU) of the event.
- The LLM's extracted `stated_date` and the exact sentence it pulled the date from.
- Up to 2 independent evidence snippets pulled from other sources (media/social) —
  note these were matched loosely and are sometimes about a different event
  entirely; ignore them if so.
- A ru.wikipedia search link and a Google search link, pre-filled with the
  region + facility + disaster-type keywords, to help you find the real date.

**What to record per item:**
- `true_date` — the real date if you can find it (YYYY-MM-DD, or partial like
  "2013-04" if that's all you can pin down). Leave blank if you can't find it.
- `matches_event` — does the stated_date match the true date? **Yes / No / Unsure.**
  Pick Unsure rather than guessing if you can't verify.
- `notes` — anything worth flagging (wrong event entirely, right date wrong
  format, ambiguous FPP text, etc).

**When done:** tap Export in the app menu. It saves (or shares, on iPad) a file
named `validation_disaster-D31-stated-date_<date>.json`. **Save it to
`~/Dropbox/_validation_exports/`** (same folder every other chunk export goes
to) — from Mac Files/Dropbox app, or AirDrop it to yourself and move it there.

**What this feeds:** the per-source date-accuracy check called for in
`disaster/notes/audit_2026-05-13.md` (search "drop sources below ~70%
accuracy"): *"When chunk E lands, run a per-source agreement check (Wikidata
vs hand, Sledcom vs hand, etc.) and drop sources below ~70% accuracy."* This
chunk is that check for the `llm_stated_date` source specifically — the single
biggest date source in the master (1,756 of ~4,235 events). If it comes back
under ~70% "Yes", that source's dates should not be trusted at day precision
without a fix.

**Loader (run after you export):**
```
Rscript disaster/code/validation/99d_load_date_validation_results.R
```
This is a new standalone loader (kept separate from the existing
`99c_load_validation_results.R` rather than editing it) — it reads your export
from `~/Dropbox/_validation_exports/`, writes
`disaster/data/processed/verification/validation_D31_stated_date_handcoded.csv`,
and prints the accuracy % against the 70% threshold.
