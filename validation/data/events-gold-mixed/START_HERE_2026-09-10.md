# START HERE — Events gold: FPP + sledcom + personnel (72 items, 2026-09-10)

**Where:** open the validation PWA (same app as every other chunk). Pick the task named
**"Events gold: FPP + sledcom + personnel (72)"** — it's now at the top of the list.

**Why one chunk, three tasks:** your hand labels are the only thing that can calibrate
the two-referee "silver" standard used across this program, and silver is now
load-bearing in three places that do NOT calibrate each other — a good read on the FPP
boundary tells us nothing about whether sledcom's `involves_official` field over-includes,
and that tells us nothing about whether rusclf's personnel filter over-fires. The three
sections are interleaved (not grouped) with a fixed seed so you don't settle into
answering one section on autopilot — no more than 4 items from the same section appear
in a row.

**Every item is ONE fast factual yes/no/unclear question about the text shown — never
a category choice, and the decision rule / model output / referee verdict is never
shown.** The question wording changes depending on which of the three sections an item
belongs to (you won't be told which section you're in, but the question itself makes it
obvious — it's shown above the text each time).

**Realistic total time: ~12 minutes of pure answering** (30 fpp items × ~5s + 20
sledcom items × ~17s, since those are longer + 15 personnel items × ~8s = 696s, computed
directly by the builder script from the actual item counts). **Budget 20–25 minutes**
in one sitting once you allow for reading time and any notes.

---

## What each section decides

### 1. FPP (30 items) — "Does the text state a crime/case/investigation/court
action/charge against this person?"

A trimmed subset of the fpp-primary-type-gold v3 chunk you may have already seen (15 of
its 30 referee-disagreement items + 8 of its 15 possible-false-positive items + 7 of its
15 possible-false-negative items). **This feeds the arrest_legal / governor_political
boundary rule that drives the arrests paper's treatment coding and the decision on
whether to deploy the newly-drafted v3 classification prompt.** If you already started
the old 67-item chunk, these 30 are a subset of what you saw — some items will repeat
(that's fine, more data).

### 2. Sledcom (20 items) — "Is a government official the DEFENDANT/SUBJECT of this
legal action, in their official capacity?"

You're shown a Sledcom (SK) press-release **title + lead paragraph** (the release is
often 1,500+ characters; you're shown the part — usually the first sentence or two after
the title — that says who is being charged). This section has three parts:

- **10 items** are the hardest, highest-value cases: rows where two independent
  frontier-model referees genuinely disagreed, mostly a "по факту" boundary (a case
  opened over an incident, citing an officials-only negligence article, before anyone
  is confirmed as the defendant).
- **6 items** are a direct human check on a live decision: **whether to drop 497 rows
  from `arrests_master`** that are currently included ONLY via a field
  (`involves_official`) that a silver audit could not validate (the audit's own
  6.5-to-1 no:yes ratio suggests most of these 497 don't actually belong). These 6 were
  deliberately picked to cover all four failure patterns the audit found — not a random
  draw — so you see the range of what's in that slice, not just the most common kind.
  **The loader states directly, with a confidence interval, what fraction of these 6
  you also judge "No" — i.e., whether you endorse the drop.**
- **4 items** are already-confirmed official-defendant cases (control — checks that you
  agree with an easy case).

### 3. Personnel (15 items) — "Does this report a change in who holds an official
position?"

Short Telegram excerpts (rusclf's own local classifier, no LLM cost) flagged as a
personnel change. A silver audit found only 60.5% of what rusclf calls a "personnel
change" holds up under independent review — **this feeds whether that 60.5% precision
is good enough to keep using rusclf for free, or whether elitesData should spend
$150–300 to re-do this with Haiku.**

- **8 items** are cases silver says are NOT a personnel change — checks that finding
  directly.
- **4 items** are the referee-split pool (this is the WHOLE pool — only 8 such items
  exist in the audited sample, you're seeing half of them).
- **3 items** are already-confirmed personnel changes (control).

---

## Repeats

**7 of the 72 items are silent exact repeats** of an earlier item, shown again later at
an unpredictable, non-adjacent position. You're not told which. Just answer each item as
it comes — the loader compares your two answers on each repeated item afterward to
measure your own test-retest agreement, separately for each of the three sections where
there are enough repeats to say anything.

## When done

Tap Export. Save the file (`validation_events-gold-mixed_<date>.json`) to
`~/Dropbox/_validation_exports/` — the same folder every other export goes to.

## What this feeds

`eventsData/code/99g_load_events_gold_mixed.R` scores each of the three sections
SEPARATELY against its own referees, silver, and production label — it does **not**
compute or print any pooled accuracy number, across sections or within a section's item
classes, because this is a deliberately targeted, non-representative sample built to
answer three specific decisions, not to estimate a corpus-wide accuracy rate.

## Status

**FPP primary_type gold (67, v3)** is still registered in the task list (renamed to
mark it superseded) but should NOT be worked on separately — its 30 highest-value items
are the ones included here. It has not been started (no export exists yet in
`~/Dropbox/_validation_exports/` as of this build), so nothing is lost by switching to
this combined chunk instead.

This chunk is built, registered, and synced into `docs/validation/` (the deployed
copy), but **not yet committed or pushed** — that's a separate step.
