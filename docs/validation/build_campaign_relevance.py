#!/usr/bin/env python3
# =============================================================================
# build_campaign_relevance.py
# Build the `campaign-relevance-A` iPad gold task — the is-campaign GATE whose
# gold unlocks a free local rusclf replacement for the ~$300-1,500 Haiku social
# relevance run (rusClassifier v3 `campaign_relevance` task).
#
# Source: campaign2026/data/processed/message_topics_raw.jsonl (Haiku silver:
#   is_campaign_relevant + confidence per message, no text). Text is joined back
#   from the rusSocial unified TG corpus by post_id (same join as
#   25_message_topics.py::run_gold_sample).
#
# Sampling: BALANCED ~125 relevant / ~125 not (the raw preds are 67/33), with the
#   boundary-uncertain cases (low/medium confidence) oversampled — maximally
#   informative for learning the gate + honest precision on BOTH classes.
# Label: DIRECT binary gold ("campaign/political message?"), not confirm/correct,
#   so the gold isn't anchored on the silver gate we're training against. Haiku's
#   call is shown only as a reference chip.
#
# Writes items.json + schema.json into both validation/ and docs/validation/.
# =============================================================================

import json, os, glob
import pandas as pd
import numpy as np
try:
    import duckdb
except Exception as e:
    raise SystemExit("need duckdb: " + str(e))
try:
    import setproctitle; setproctitle.setproctitle("campaign_relevance_builder")
except Exception:
    pass

SEED = 20260706
rng = np.random.default_rng(SEED)

PROJ = os.path.expanduser("~/Dropbox/Projects")
RAW  = os.path.join(PROJ, "campaign2026/data/processed/message_topics_raw.jsonl")
TG_GLOB = os.path.join(PROJ, "rusSocial/data/processed/unified/source=telegram/post_type=post/year_month=*/*.parquet")
SRC_ROOT  = os.path.join(PROJ, "me/website/validation/data")
DOCS_ROOT = os.path.join(PROJ, "me/website/docs/validation/data")
TASK_ID   = "campaign-relevance-A"

N_POS, N_NEG = 50, 50   # one ~100 chunk; deploy a 2nd chunk when this one's done

def emit(task_id, schema, items):
    for root in (SRC_ROOT, DOCS_ROOT):
        d = os.path.join(root, task_id); os.makedirs(d, exist_ok=True)
        json.dump(schema, open(os.path.join(d, "schema.json"), "w"), ensure_ascii=False, indent=2)
        json.dump(items,  open(os.path.join(d, "items.json"),  "w"), ensure_ascii=False, indent=1)
    print(f"  [{task_id}] wrote {len(items)} items -> src + docs")

def take(df, n):
    n = min(n, len(df))
    return df.sample(n, random_state=SEED) if n else df.iloc[:0]

def main():
    recs = [json.loads(l) for l in open(RAW, encoding="utf-8") if l.strip()]
    d = pd.DataFrame(recs).drop_duplicates(subset="post_id", keep="last")
    d["rel"] = d["is_campaign_relevant"].astype(str)     # "True"/"False"
    d["conf"] = d["confidence"].astype(str)
    d["uncertain"] = d["conf"].isin(["low", "medium"])

    pos = d[d["rel"] == "True"]; neg = d[d["rel"] == "False"]
    # negatives: keep ALL uncertain (scarce boundary negatives) + fill with high-conf
    neg_unc = neg[neg["uncertain"]]
    neg_hi  = take(neg[~neg["uncertain"]], N_NEG - len(neg_unc))
    neg_sel = pd.concat([neg_unc, neg_hi])
    # positives: all low + oversample medium + a slice of high
    pos_low = pos[pos["conf"] == "low"]
    pos_med = take(pos[pos["conf"] == "medium"], max(0, int(N_POS * 0.6)))   # oversample the uncertain
    pos_hi  = take(pos[pos["conf"] == "high"], max(0, N_POS - len(pos_low) - len(pos_med)))
    pos_sel = pd.concat([pos_low, pos_med, pos_hi])

    sel = pd.concat([pos_sel.assign(_cls="relevant"), neg_sel.assign(_cls="not")])
    sel = sel.sample(frac=1, random_state=SEED).reset_index(drop=True)   # interleave classes
    print(f"  selected {len(sel)}: {(sel['rel']=='True').sum()} relevant / {(sel['rel']=='False').sum()} not; "
          f"uncertain={sel['uncertain'].sum()}")

    # ---- join post text from the rusSocial TG corpus by post_id ----
    ids = [str(x) for x in sel["post_id"].dropna().tolist()]
    if not glob.glob(TG_GLOB):
        raise SystemExit(f"TG corpus glob empty (dehydrated?): {TG_GLOB}")
    con = duckdb.connect(); con.execute("SET memory_limit='4GB';")
    con.execute("CREATE TEMP TABLE want(pid VARCHAR)")
    con.executemany("INSERT INTO want VALUES (?)", [(i,) for i in ids])
    txt = con.execute(f"""
        SELECT CAST(post_id AS VARCHAR) pid,
               left(replace(COALESCE(text,''), chr(10), ' '), 1000) AS snippet
        FROM read_parquet('{TG_GLOB}', union_by_name=true)
        WHERE CAST(post_id AS VARCHAR) IN (SELECT pid FROM want)
    """).df()
    con.close()
    sel["post_id"] = sel["post_id"].astype(str)
    sel = sel.merge(txt, left_on="post_id", right_on="pid", how="left")
    n_notext = sel["snippet"].isna().sum()
    print(f"  text join: {len(sel)-n_notext}/{len(sel)} matched; dropping {n_notext} with no text")
    sel = sel[sel["snippet"].notna() & (sel["snippet"].str.len() > 0)].reset_index(drop=True)

    items = []
    for ix in range(len(sel)):
        r = sel.iloc[ix]
        items.append({
            "post_id": str(r["post_id"]),
            "bucket": f"{'relevant' if r['rel']=='True' else 'not'}/{r['conf']}",
            "date": ("" if pd.isna(r.get("date")) else str(r["date"])),
            "party_slug": ("" if pd.isna(r.get("party_slug")) else str(r["party_slug"])),
            "regionid": (None if pd.isna(r.get("regionid")) else int(r["regionid"])),
            "text": str(r["snippet"]),
            "pred_relevant": str(r["is_campaign_relevant"]),
            "pred_primary": ("" if pd.isna(r.get("primary_topic")) else str(r["primary_topic"])),
            "confidence": str(r["conf"]),
        })

    schema = {
        "task_id": TASK_ID,
        "name": "Campaign relevance gate — is this a campaign message? (%d)" % len(items),
        "version": "2026-07-06",
        "id_field": "post_id",
        "instructions": ("The GATE that decides which posts count as campaign/political messaging. "
            "Judge DIRECTLY from the text (Haiku's guess is shown only for reference — don't defer to it). "
            "YES = the post is political/campaign content: policy, candidate/party promotion, grievances, "
            "voter mobilisation, attacks on opponents, ideology. NO = admin/service notice, bare repost with "
            "no stance, ad, holiday greeting, weather, non-political filler. Sample is balanced ~50/50 and "
            "oversamples low/medium-confidence boundary cases — the ones that teach the gate the most. This "
            "gold trains the free local classifier that replaces the paid Haiku relevance run."),
        "display": [
            {"field": "bucket", "label": "Bucket", "format": "tag"},
            {"field": "date", "label": "Date", "format": "compact"},
            {"field": "party_slug", "label": "Party", "format": "compact"},
            {"field": "regionid", "label": "regionid", "format": "compact"},
            {"field": "text", "label": "Post (RU)", "format": "longtext"},
            {"field": "pred_relevant", "label": "Haiku: campaign?", "format": "compact", "highlight": "llm"},
            {"field": "pred_primary", "label": "Haiku: topic (context)", "format": "compact"},
            {"field": "confidence", "label": "Haiku conf", "format": "compact"},
            {"field": "post_id", "label": "post_id", "format": "compact"},
        ],
        "validation": [
            {"field": "relevant", "label": "Campaign / political message?", "type": "enum", "required": True,
             "options": [
                {"value": "yes", "label": "Yes — campaign/political", "key": "1", "tone": "good"},
                {"value": "no",  "label": "No — filler/admin/ad", "key": "2", "tone": "bad"},
                {"value": "cant_tell", "label": "Can't tell", "key": "3", "tone": "neutral"}]},
            {"field": "notes", "label": "Notes", "type": "textarea",
             "placeholder": "Borderline reposts, mixed, sarcasm…"},
        ],
    }
    emit(TASK_ID, schema, items)

if __name__ == "__main__":
    print("Building campaign-relevance-A (seed=%d)…" % SEED)
    main()
    print("Done.")
