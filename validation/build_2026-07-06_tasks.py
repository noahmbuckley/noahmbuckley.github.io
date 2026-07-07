#!/usr/bin/env python3
# =============================================================================
# build_2026-07-06_tasks.py
# Generate 3 new iPad-validation PWA tasks from ready source data, with
# DIVERGENT / informative sampling (hard cases first, strata tagged so an
# unbiased estimate is still recoverable by reweighting). Writes items.json +
# schema.json into BOTH the source tree (validation/data/<id>/) and the
# published mirror (docs/validation/data/<id>/). Does NOT touch tasks.json
# (registered separately) or push anything.
#
#   topics-A       campaign2026 message topic gold (150)   confirm/correct
#   dedup-A        elitesData person-merge verdicts (150)  same/different, hard-first
#   disaster-date-A disaster LLM date-evidence check (60)  does quote support the date
#
# Reproducible: fixed seed. Base R style N/A (Python grunt I/O per parent CLAUDE.md).
# =============================================================================

import json, os, sys, hashlib
import pandas as pd
import numpy as np

setproctitle_ok = True
try:
    import setproctitle; setproctitle.setproctitle("validation_task_builder")
except Exception:
    setproctitle_ok = False

SEED = 20260706
np.random.seed(SEED)

PROJ = os.path.expanduser("~/Dropbox/Projects")
SRC_ROOT  = os.path.join(PROJ, "me/website/validation/data")
DOCS_ROOT = os.path.join(PROJ, "me/website/docs/validation/data")

def emit(task_id, schema, items):
    """Write schema.json + items.json (plain array) into both trees."""
    for root in (SRC_ROOT, DOCS_ROOT):
        d = os.path.join(root, task_id)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "schema.json"), "w") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        with open(os.path.join(d, "items.json"), "w") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"  [{task_id}] wrote {len(items)} items -> src + docs")

def clip(s, n=1200):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[:n] + " …[truncated]"


# =============================================================================
# 1. topics-A  — campaign message topic gold (confirm/correct, hard-first)
# =============================================================================
def build_topics():
    csv = os.path.join(PROJ, "campaign2026/validation/topics_gold_template_2026-06-27.csv")
    d = pd.read_csv(csv)
    # hard-first: medium confidence, then multi-topic, then the rest
    d["_multi"] = d["pred_topics"].fillna("").str.contains(r"\|")
    d["_conf_rank"] = d["pred_confidence"].map({"low":0,"medium":1,"high":2}).fillna(1)
    d = d.sort_values(["_conf_rank","_multi"], ascending=[True, False]).reset_index(drop=True)

    TOPICS = ["agriculture_industry","corruption_accountability","ecology","economy_prices",
              "education","election_process","healthcare","housing_utilities",
              "infrastructure_transport","migration","opposition_repression","other",
              "patriotism_values","social_welfare","svo_war","youth_sport_culture"]

    items = []
    for ix in range(len(d)):
        r = d.iloc[ix]
        items.append({
            "src_id": str(r["src_id"]),
            "conf_rank": ("medium/low" if r["_conf_rank"] < 2 else "high"),
            "date": ("" if pd.isna(r["date"]) else str(r["date"])),
            "party_slug": ("" if pd.isna(r["party_slug"]) else str(r["party_slug"])),
            "regionid": (None if pd.isna(r["regionid"]) else int(r["regionid"])),
            "text": clip(r["text"]),
            "pred_relevant": ("" if pd.isna(r["pred_relevant"]) else str(r["pred_relevant"])),
            "pred_primary": ("" if pd.isna(r["pred_primary"]) else str(r["pred_primary"])),
            "pred_topics": ("" if pd.isna(r["pred_topics"]) else str(r["pred_topics"])),
            "pred_confidence": ("" if pd.isna(r["pred_confidence"]) else str(r["pred_confidence"])),
        })

    schema = {
        "task_id": "topics-A",
        "name": "Campaign message topics — confirm/correct (150)",
        "version": "2026-07-06",
        "id_field": "src_id",
        "instructions": ("Each row is a party/candidate social post. Yellow = Haiku's IS-CAMPAIGN call "
            "and its PRIMARY topic (16-topic taxonomy). Confirm or correct. Sorted HARD-FIRST "
            "(medium/low-confidence + multi-topic up top — the informative ones). "
            "Relevance: is this genuine campaign/political messaging (vs a bare repost, ad, "
            "greeting, service notice)? Primary topic: the DOMINANT issue. Blank primary-correction = "
            "Haiku's primary is right. Anchoring caveat: Haiku's guess is shown for speed — trust the "
            "text over the chip."),
        "display": [
            {"field": "conf_rank", "label": "Bucket", "format": "tag"},
            {"field": "date", "label": "Date", "format": "compact"},
            {"field": "party_slug", "label": "Party", "format": "compact"},
            {"field": "regionid", "label": "regionid", "format": "compact"},
            {"field": "text", "label": "Post (RU)", "format": "longtext"},
            {"field": "pred_relevant", "label": "Haiku: campaign?", "format": "compact", "highlight": "llm"},
            {"field": "pred_primary", "label": "Haiku: primary topic", "format": "compact", "highlight": "llm"},
            {"field": "pred_topics", "label": "Haiku: all topics", "format": "compact"},
            {"field": "pred_confidence", "label": "Haiku conf", "format": "compact"},
            {"field": "src_id", "label": "id", "format": "compact"},
        ],
        "validation": [
            {"field": "relevant_correct", "label": "Is-campaign call correct?", "type": "enum", "required": True,
             "options": [
                {"value": "yes", "label": "Yes", "key": "1", "tone": "good"},
                {"value": "no",  "label": "No",  "key": "2", "tone": "bad"},
                {"value": "cant_tell", "label": "Can't tell", "key": "3", "tone": "neutral"}]},
            {"field": "primary_correct", "label": "Primary topic correct?", "type": "enum", "required": True,
             "options": [
                {"value": "yes", "label": "Yes", "key": "4", "tone": "good"},
                {"value": "no",  "label": "No",  "key": "5", "tone": "bad"},
                {"value": "na",  "label": "n/a (not campaign)", "key": "6", "tone": "neutral"}]},
            {"field": "correct_primary", "label": "Correct primary (if wrong)", "type": "enum",
             "options": [{"value": t, "label": t, "tone": "neutral"} for t in TOPICS],
             "show_if": {"primary_correct": ["no"]}},
            {"field": "notes", "label": "Notes", "type": "textarea",
             "placeholder": "Sarcasm, mixed topics, edge cases…"},
        ],
    }
    emit("topics-A", schema, items)


# =============================================================================
# 2. dedup-A  — elitesData person-merge verdicts (hard-first: smallest score_gap)
# =============================================================================
def build_dedup(n=150):
    csv = os.path.join(PROJ, "elitesData/validation/dedup_sample_2026-06-30.csv")
    d = pd.read_csv(csv)
    # Most informative = ambiguous matches: smallest score_gap between top match and runner-up.
    d["score_gap"] = pd.to_numeric(d["score_gap"], errors="coerce")
    d["_gap"] = d["score_gap"].fillna(d["score_gap"].max() if d["score_gap"].notna().any() else 0.0)
    d = d.sort_values("_gap", ascending=True).reset_index(drop=True)
    hard = d.head(int(n * 0.8))                       # 120 most ambiguous
    rest = d.iloc[int(n * 0.8):]
    calib = rest.sample(min(n - len(hard), len(rest)), random_state=SEED) if len(rest) else rest.iloc[:0]
    sel = pd.concat([hard.assign(_stratum="ambiguous"), calib.assign(_stratum="calibration")])
    sel = sel.reset_index(drop=True)

    items = []
    for ix in range(len(sel)):
        r = sel.iloc[ix]
        rid = f"{r['src']}::{r['src_id']}"
        items.append({
            "row_id": rid,
            "stratum": r["_stratum"],
            "sample_tier": str(r.get("sample_tier","")),
            "incoming": " ".join(str(x) for x in [r.get("incoming_surname",""), r.get("incoming_given",""),
                                                  r.get("incoming_patr","")] if str(x) not in ("","nan")),
            "incoming_region": (None if pd.isna(r.get("incoming_regionid")) else int(r["incoming_regionid"])),
            "spine_names": clip(r.get("spine_names",""), 400),
            "spine_patr": str(r.get("spine_patr","")),
            "spine_regions": str(r.get("spine_regions","")),
            "spine_roles": clip(r.get("spine_roles",""), 300),
            "spine_nrec": (None if pd.isna(r.get("spine_nrec")) else int(r["spine_nrec"])),
            "match_basis": str(r.get("match_basis","")),
            "match_score": (None if pd.isna(r.get("match_score")) else float(r["match_score"])),
            "score_gap": (None if pd.isna(r.get("score_gap")) else float(r["score_gap"])),
        })

    schema = {
        "task_id": "dedup-A",
        "name": "Elite person-merge — same or different? (150)",
        "version": "2026-07-06",
        "id_field": "row_id",
        "instructions": ("An INCOMING elite record (left) was matched to a person already on the registry "
            "spine (right). Is it the SAME human? Sorted HARD-FIRST by smallest score_gap (the top match "
            "barely beat the runner-up — the ambiguous calls that teach the matcher the most). "
            "match_basis: 2tok=surname+given only; +patr adds patronymic; region+2tok adds region; "
            "qid=Wikidata id. SAME = merge; DIFFERENT = two people wrongly merged (split); "
            "UNSURE if the spine record is too thin to judge."),
        "display": [
            {"field": "stratum", "label": "Stratum", "format": "tag"},
            {"field": "sample_tier", "label": "Tier", "format": "compact"},
            {"field": "incoming", "label": "INCOMING person", "format": "compact", "highlight": "llm"},
            {"field": "incoming_region", "label": "incoming regionid", "format": "compact"},
            {"field": "spine_names", "label": "SPINE name(s)", "format": "longtext"},
            {"field": "spine_patr", "label": "spine patronymic", "format": "compact"},
            {"field": "spine_regions", "label": "spine region(s)", "format": "compact"},
            {"field": "spine_roles", "label": "spine role(s)", "format": "longtext"},
            {"field": "spine_nrec", "label": "spine #records", "format": "compact"},
            {"field": "match_basis", "label": "match basis", "format": "compact"},
            {"field": "match_score", "label": "score", "format": "compact"},
            {"field": "score_gap", "label": "gap to runner-up", "format": "compact"},
        ],
        "validation": [
            {"field": "verdict", "label": "Same person?", "type": "enum", "required": True,
             "options": [
                {"value": "same", "label": "Same (merge)", "key": "1", "tone": "good"},
                {"value": "different", "label": "Different (split)", "key": "2", "tone": "bad"},
                {"value": "unsure", "label": "Unsure / thin", "key": "3", "tone": "warn"}]},
            {"field": "notes", "label": "Notes", "type": "textarea",
             "placeholder": "Which field decided it; namesake collisions…"},
        ],
    }
    emit("dedup-A", schema, items)


# =============================================================================
# 3. disaster-date-A — does the quoted evidence support the LLM's event date? (60)
# =============================================================================
def build_disaster_date(n=60):
    jl = os.path.join(PROJ, "disaster/data/processed/verification/event_details_extracted.jsonl")
    recs = [json.loads(l) for l in open(jl)]
    df = pd.DataFrame(recs)
    df = df[df["date_evidence"].notna() & (df["date_evidence"].astype(str).str.len() > 0)].copy()
    # Divergent: prioritise the uncertain calls — low/medium confidence and/or evidence_matches_event False.
    df["_hard"] = (~df["confidence"].isin(["high"])) | (df["evidence_matches_event"].astype(str) != "True")
    hard = df[df["_hard"]]
    easy = df[~df["_hard"]]
    take_hard = hard.sample(min(int(n*0.8), len(hard)), random_state=SEED)
    take_easy = easy.sample(min(n - len(take_hard), len(easy)), random_state=SEED) if len(easy) else easy.iloc[:0]
    sel = pd.concat([take_hard.assign(_stratum="uncertain"), take_easy.assign(_stratum="confident")]).reset_index(drop=True)

    items = []
    for ix in range(len(sel)):
        r = sel.iloc[ix]
        items.append({
            "eventid": int(r["eventid"]),
            "stratum": r["_stratum"],
            "stated_event_date": ("" if pd.isna(r.get("stated_event_date")) else str(r["stated_event_date"])),
            "date_evidence": clip(r.get("date_evidence",""), 800),
            "summary": clip(r.get("summary",""), 800),
            "cause": ("" if pd.isna(r.get("cause")) else str(r["cause"])),
            "facility": clip(r.get("facility",""), 400),
            "deaths": ("" if pd.isna(r.get("deaths")) else str(r["deaths"])),
            "confidence": ("" if pd.isna(r.get("confidence")) else str(r["confidence"])),
            "evidence_matches_event": str(r.get("evidence_matches_event","")),
        })

    schema = {
        "task_id": "disaster-date-A",
        "name": "Disaster date — does the evidence support it? (60)",
        "version": "2026-07-06",
        "id_field": "eventid",
        "instructions": ("Haiku extracted an event DATE (yellow) and quoted the EVIDENCE it used. "
            "Judge only ONE thing: does the quoted evidence actually support that date for THIS event? "
            "Sorted uncertain-first (low/medium confidence or evidence_matches_event≠True). "
            "yes = quote clearly dates this event; partial = right event, vague/indirect date; "
            "no = quote doesn't support the date (or is a different event); can't-tell = quote too thin. "
            "If no/partial and you can read the right date off the quote, type it."),
        "display": [
            {"field": "stratum", "label": "Stratum", "format": "tag"},
            {"field": "stated_event_date", "label": "Haiku date", "format": "compact", "highlight": "llm"},
            {"field": "date_evidence", "label": "Quoted evidence (RU)", "format": "longtext"},
            {"field": "summary", "label": "Event summary", "format": "longtext"},
            {"field": "cause", "label": "Cause", "format": "compact"},
            {"field": "facility", "label": "Facility/place", "format": "compact"},
            {"field": "deaths", "label": "Deaths", "format": "compact"},
            {"field": "confidence", "label": "Haiku conf", "format": "compact"},
            {"field": "evidence_matches_event", "label": "ev matches event?", "format": "compact"},
            {"field": "eventid", "label": "eventid", "format": "compact"},
        ],
        "validation": [
            {"field": "date_supported", "label": "Evidence supports the date?", "type": "enum", "required": True,
             "options": [
                {"value": "yes", "label": "Yes", "key": "1", "tone": "good"},
                {"value": "partial", "label": "Partial", "key": "2", "tone": "warn"},
                {"value": "no", "label": "No", "key": "3", "tone": "bad"},
                {"value": "cant_tell", "label": "Can't tell", "key": "4", "tone": "neutral"}]},
            {"field": "correct_date", "label": "Correct date (YYYY-MM-DD, if readable)", "type": "text",
             "placeholder": "e.g. 2012-12-26", "show_if": {"date_supported": ["no","partial"]}},
            {"field": "notes", "label": "Notes", "type": "textarea", "placeholder": "Ambiguities…"},
        ],
    }
    emit("disaster-date-A", schema, items)


if __name__ == "__main__":
    print("Building validation tasks (seed=%d, setproctitle=%s)…" % (SEED, setproctitle_ok))
    build_topics()
    build_dedup()
    build_disaster_date()
    print("Done.")
