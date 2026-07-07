#!/usr/bin/env python3
# =============================================================================
# tidy_shortlist_2026-07-06.py
# Reduce the iPad validation app to a SHORT, prioritized list of fresh ~100-item
# chunks. Wipes every other task dir from both trees and rewrites tasks.json to
# exactly the shortlist. Run build_campaign_relevance.py (→100) FIRST.
#
#   SHORTLIST (display order = priority):
#     1 campaign-relevance-A            100  is-campaign GATE  (rusclf v3; $ payoff)
#     2 sentiment-prompt-comparison     100  RuBERT-tiny2 sentiment (pub blocker)
#     3 channel-actor-A                 110  rusclf v3 (silver is biased → gold essential)
#     4 courts-extract-A                120  rusclf v3 (first court gold)
#     5 rusSocial-responsibility-blind   81  disaster blame-attribution
#
# On deck (rebuild fresh when the shortlist clears): topics, dedup, disaster-date,
# event-type, campaign-relevance-B, sentiment-B. Builders: build_2026-07-06_tasks.py,
# build_campaign_relevance.py.
# =============================================================================

import json, os, shutil

PROJ = os.path.expanduser("~/Dropbox/Projects")
TREES = [os.path.join(PROJ, "me/website/validation"),
         os.path.join(PROJ, "me/website/docs/validation")]

SHORTLIST = [
    ("campaign-relevance-A", "campaign2026",
     "Campaign relevance GATE — is this a campaign/political message? (~100)",
     "PRIORITY 1. Direct binary gold for the is-campaign gate — unlocks a free local classifier to replace the ~$300-1,500 Haiku relevance run. Balanced 50/50, boundary-oversampled. Judge from the text."),
    ("sentiment-prompt-comparison", "rusSocial",
     "Sentiment — 3-class, 5-model check (~100)",
     "PRIORITY 2. Anchors RuBERT-tiny2 accuracy + its neutral-over-prediction bias (the standing publication blocker). ~75 model-disagreement rows + ~25 all-agree anchor."),
    ("channel-actor-A", "rusClassifier",
     "Channel actor-type — confirm/correct (110)",
     "PRIORITY 3. rusclf v3 gold. The username rule mislabels regional NEWS channels as party/ER — your corrections are the ONLY clean news/not_political negatives. Code the negatives deliberately."),
    ("courts-extract-A", "rusClassifier",
     "Court decision extraction — confirm/correct (120)",
     "PRIORITY 4. First-ever gold for court-decision extraction (verdict/sentence/fine/articles). Feeds a rusclf v3 court slice → then the full 122K corpus runs $0 local."),
    ("rusSocial-responsibility-blind", "rusSocial",
     "Blame attribution — BLIND (81)",
     "PRIORITY 5. Does a disaster post attribute responsibility, to whom, how strongly + futility? No Haiku shown (unbiased κ). Unblocks the disaster paper's per-event blame consumption."),
]
KEEP = {t[0] for t in SHORTLIST}

# ---- 1. resize sentiment to a ~100 chunk (most-divergent 100, with an anchor) ----
def resize_sentiment():
    src = os.path.join(TREES[0], "data/sentiment-prompt-comparison/items.json")
    items = json.load(open(src))
    by = {"haiku_internal_disagree": [], "tiny_vs_haiku_disagree": [], "all_agree": [], "_o": []}
    for it in items:
        by.get(it.get("stratum_label"), by["_o"]).append(it)
    # deterministic order by post_id within each stratum
    for k in by: by[k].sort(key=lambda x: str(x.get("post_id")))
    sel = by["haiku_internal_disagree"][:40] + by["tiny_vs_haiku_disagree"][:40] + by["all_agree"][:20]
    # top up to 100 from leftovers if any stratum was short
    if len(sel) < 100:
        pool = (by["tiny_vs_haiku_disagree"][40:] + by["haiku_internal_disagree"][40:]
                + by["all_agree"][20:] + by["_o"])
        sel += pool[:100 - len(sel)]
    sel = sel[:100]
    for tree in TREES:
        p = os.path.join(tree, "data/sentiment-prompt-comparison/items.json")
        json.dump(sel, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"  sentiment resized -> {len(sel)} items (both trees)")

# ---- 2. rewrite tasks.json to exactly the shortlist ----
def write_registry():
    tasks = [{"id": tid, "name": name, "project": proj,
              "description": desc,
              "schema_url": f"data/{tid}/schema.json",
              "items_url": f"data/{tid}/items.json"} for (tid, proj, name, desc) in SHORTLIST]
    reg = {"schema_version": 1, "generated_at": "2026-07-06", "tasks": tasks}
    for tree in TREES:
        json.dump(reg, open(os.path.join(tree, "tasks.json"), "w"), ensure_ascii=False, indent=2)
    print(f"  registry rewritten -> {len(tasks)} tasks (both trees)")

# ---- 3. delete every other task dir from both trees ----
def prune_dirs():
    for tree in TREES:
        ddir = os.path.join(tree, "data")
        removed = []
        for name in sorted(os.listdir(ddir)):
            p = os.path.join(ddir, name)
            if os.path.isdir(p) and name not in KEEP:
                shutil.rmtree(p); removed.append(name)
        print(f"  {os.path.basename(os.path.dirname(tree))}/{os.path.basename(tree)}: removed {len(removed)} dirs")
        if removed: print("    " + ", ".join(removed))

if __name__ == "__main__":
    print("Tidying validation app to the shortlist…")
    resize_sentiment()
    write_registry()
    prune_dirs()
    # verify
    for tree in TREES:
        reg = json.load(open(os.path.join(tree, "tasks.json")))["tasks"]
        for t in reg:
            for u in (t["schema_url"], t["items_url"]):
                assert os.path.exists(os.path.join(tree, u)), f"MISSING {tree}/{u}"
            n = len(json.load(open(os.path.join(tree, t["items_url"]))))
            print(f"    {t['id']:34s} {n} items  [{tree.split('/')[-2]}]")
    print("Done.")
