# START HERE — Disaster response-markers validation

**Where:** open the validation PWA (same app as the D-31 stated-date chunk).
Pick the task named **"Disaster response-markers validation (~60)"**.

**What it is:** 60 disaster events where a Haiku LLM pass read matched news/
social snippets and tagged government-response markers (CHS/emergency-regime
declared, governor on-site, federal attention) — nobody has checked whether
the underlying snippets actually describe a response to THIS event, or
whether the marker is right. Stratified by deaths bracket x Haiku-yes/no on
CHS x Haiku-yes/no on federal attention, oversampling high-severity and
CHS=yes events.

**Per event you will see:**
- FPP/summary description (RU), disaster type, deaths, event date.
- The Haiku CHS / federal-attention calls.
- Up to 3 supporting snippets, each tagged with which marker it was pulled
  for (governor-onsite / CHS / federal). These come from the *regex* first
  pass, which is what fed the Haiku LLM prompt, so checking the regex
  snippet is checking what the LLM actually saw.
- ru.wikipedia and Google search links.

**What to record per item:**
- `snippet_matches_event` — do the snippets actually describe a response to
  THIS event? Yes / Some / No.
- `confirmed_markers` — free-text list of markers you can confirm as genuinely
  present (e.g. "governor_onsite, chs"), blank if none confirmed.
- `notes` — anything worth flagging.

**When done:** Export from the app menu, save to
`~/Dropbox/_validation_exports/` (same convention as every other chunk).

**What this feeds:** the coverage/agreement tables in
`disaster/notes/response_master_build_2026-09-15.md` and
`disaster/data/processed/response/event_response_master.csv` — this is the
first human check of the Haiku response-marker layer (4,235-event Haiku
Batches pass, commit 3e18e1cb). Build script:
`disaster/code/response/08_build_response_validation_chunk.R`.

