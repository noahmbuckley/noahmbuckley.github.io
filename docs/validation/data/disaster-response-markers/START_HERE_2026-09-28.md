# START HERE — Disaster response-markers validation (v2, rebuilt 2026-09-28)

**Supersedes** `START_HERE_2026-09-15.md` (old chunk = v1 Haiku calls, regex snippets, 8-char
region names; archived as `items_v1_2026-09-15.json.bak`). Same task in the app:
**"Disaster response-markers validation v2 (66)"**.

## What it checks
A Haiku prompt-v2 pass read up to ~30 days of matched news/social snippets per event and called
7 government-response markers `yes` / `no` (explicit denial only) / `unclear`. Two are gated in
the draft PAP addendum 5: **chs_declared** (ЧС / emergency regime formally declared) and
**federal_attention** (president / RF government / federal minister / federal HQ of an agency;
a regional branch does not count). You check (a) **precision** of the YES calls and (b)
**recall** — is a marker present where the model said nothing?

## What you see per event
FPP text, the event summary the model was given, the model's calls with the quote and snippet
it cited, and **the snippets the model actually saw** (re-packaged from the evidence corpus and
asserted identical to the logged snippet list; cited ones first; window = 1 day before to 30
days after the "event date"). The "event date" is the window anchor the pipeline used, NOT
necessarily the true date: if it is wrong the snippets cover the wrong weeks (e.g. Krymsk 7932
is anchored on 2013-04-22, the trial month). If the window is off, answer "No / wrong event" for
relevance and tell me in the notes.

## Sample (66 items; strata mutually exclusive)
| stratum | rule | pool | shown |
|---|---|---:|---:|
| C | chs_declared = yes | 230 | 20 |
| F | federal = yes, chs not yes | 609 | 18 |
| G | governor / compensation / dismissal / mourning yes only | 196 | 6 |
| I | investigation-only yes | 313 | 3 |
| N1 | NO marker; model marked ≥1 snippet relevant (recall) | 985 | 10 |
| N2 | NO marker; model marked no snippet relevant (recall) | 1,450 | 9 |

Within a stratum, deaths brackets (10+ / 2–9 / 0–1 / unknown) are oversampled where a count is
known (69% of events have none); design weights are stored. The 452 events with no snippet in
the window (all-unclear by rule) are not in the sample — nothing to judge.

## What to record
- **Snippets describe THIS event?** yes / some / no (every item).
- **CHS = YES correct?** and **FEDERAL = YES correct?** (shown only when the model said yes): Correct / Not supported / Can't tell. "Correct" = the cited snippet is about THIS event and states the marker.
- **Other YES markers:** all supported / at least one not / none shown; list unsupported ones.
- **All-unclear items:** is a response marker actually present (no / yes / can't tell)?
- **Missed markers:** name any marker present that the model called unclear.

## DECISION RULE (pre-declared 2026-09-28, before any coding)
Source: `disaster/preregistration/preanalysis_plan_addendum_2026-09-15_DRAFT_response_and_attention.md`
§2(iii), also `audit_fixlist_2026-09-15b.md` Fix 6: *"the 60-event iPad set must show Haiku marker
precision ≥ 0.8 on ЧС and federal attention, or those markers move to 'exploratory'."*
> **Caveats — CC flags:** that addendum is an unsealed DRAFT; "precision" is not defined there;
> the pilot's definition (audit / 09-15 pilot note) is "yes-markers that follow from an event-relevant
> snippet". Operationalisation below is CC's proposal for Noah to confirm before coding.

1. **Precision (per gated marker)** = share of that marker's YES calls you mark *Correct*
   among those marked Correct or Not supported ("Can't tell" excluded and its count reported).
2. **Estimate** = design-weighted (cell weights in the items), with a stratified-bootstrap 95% CI;
   the unweighted Wilson CI is printed beside it.
3. **Gate:** each of chs_declared and federal_attention needs weighted precision **≥ 0.80** (the
   draft's literal bar = point estimate); otherwise that marker is "exploratory". The CI is
   reported, not used to redefine the bar.
4. **Power flag:** ~20 CHS-yes and ~28 federal-yes calls are shown, so the CI will be roughly ±0.15–0.2.
   A point estimate within ±0.1 of 0.80 is not decisive; if that happens, extending the sample is
   the honest option, not a re-read of the bar.
5. Other markers (governor, compensation, investigation, dismissal, mourning): no bar in any doc.
   Reported descriptively (item-level "all supported").
6. **Recall:** no bar declared anywhere. Reported as the design-weighted share of no-marker events
   where you find a marker present — descriptive only.

## Export and load
Menu → Export → save to `~/Dropbox/_validation_exports/`. Then
`Rscript disaster/code/response/08b_load_response_validation_results.R` (new loader; writes
`disaster/data/processed/response/validation_response_markers_handcoded.csv`, prints the four tables).
