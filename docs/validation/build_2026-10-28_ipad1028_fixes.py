#!/usr/bin/env python3
##### build_2026-10-28_ipad1028_fixes.py #####
# IPAD1028-D1 = a, D2 = a, D3 = a (Noah, 2026-10-28). Display-only rebuild of three live tasks after
# Noah's 2026-10-27 sitting stalled on the instruments (_notes/ipad_feedback_2026-10-28.md):
#   disaster-D31-stated-date-41   : "evidence snippets" (first two unranked retrieval items, unrelated on
#                                   ~18/35 cards) replaced by the extractor's own source item, located by
#                                   matching the quoted sentence; quote + summary hidden on the 6
#                                   two-date cards (they named the extractor's side); plain start box;
#                                   the 6 cards coded "unsure" because of the snippets are reset once (D2).
#   arrests-case-linkage-S1-24    : A/B texts extended from the 250-char corpus copy to the source's
#                                   500-char excerpt (Telegram) + a link to the original post/article;
#                                   plain start box saying most S1 cards have no B by design (D3 a).
#   gold-elvis-1022-subset96      : real post for mayor cards (roster stored the city, in Latin letters),
#                                   level codes in Russian, Telegram markdown stripped; plain start box.
# Same items, same order, same ids; no model verdicts added. Old schema/items kept as *.pre_ipad1028.
#
# Inputs fetched from the cloud (not synced on the mini) into SCRATCH:
#   rclone copy dropbox:Projects/disaster/data/processed/verification/evidence/event_evidence.jsonl
#   rclone copy dropbox:Projects/disaster/data/processed/verification/evidence/event_evidence.pre_d69_20260929.jsonl
#   rclone copy dropbox:Projects/eventsData/output/rusmedia_arrest_articles.csv
#   tg_found.json  = rows of dropbox:Projects/eventsData/output/telegram_arrest_posts.csv for the needed ids
#   need_ids.json  = (item_id, slot, source_id) for the 24 S1 cards (KEY a_source_id; B by text match)
# Run: /usr/bin/python3 build_2026-10-28_ipad1028_fixes.py ~/scratch_ipad1028

import csv
import json
import os
import re
import shutil
import sys
from difflib import SequenceMatcher

# === PATHS AND SETUP ===
APP = "/Users/noahbuckley/Dropbox/Projects/me/website/validation/data"
SCRATCH = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/scratch_ipad1028")
D31 = os.path.join(APP, "disaster-D31-stated-date-41")
CLP = os.path.join(APP, "arrests-case-linkage-S1-24")
ELV = os.path.join(APP, "gold-elvis-1022-subset96")
CLP_KEY = "/Users/noahbuckley/Dropbox/Projects/arrestsPubOpinionPaper/validation/case_linkage_pairs_stage_2026-10-04/KEY_BLIND_do_not_open_2026-10-04.csv"
RESET_BEFORE = "2026-10-28T02:10:00Z"   # deploy time (review 10-28): every answer saved before the fixed cards went live
D31_RESET = ["d31_51060", "d31_75204", "d31_11684", "d31_72599", "d31_24", "d31_53274",   # IPAD1028-D2 a
             "d31k_81564"]   # two-date card answered while the extractor's quote named its side (IPAD1028-D5)
CLP_RESET = ["clp_69168", "clp_66125", "clp_33030"]   # answered on the 250-char text, now longer + link
ELV_RESET = ["GE217"]                                 # notes-only answer on the old card
# Display-only: the loaders merge every export and keep the latest answer per card, so a reset card the
# coder does not re-code keeps its 10-27 answer; nothing is lost (the 10-27 exports stay in _validation_exports).
B_SID_OVERRIDE = {("clp_87411", "b2"): "sh_76_ru_69938258"}   # two text matches; the card labels B2 Shkulev
csv.field_size_limit(10 ** 9)


def backup(path):
    bak = path + ".pre_ipad1028"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    return bak


def load_json(path):
    return json.load(open(backup(path), encoding="utf-8"))   # always rebuild from the pre-fix copy


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)


def split_admin(instr):
    # leading "[...]" blocks are bookkeeping for CC, not guidance for the coder
    admin = []
    while instr.startswith("["):
        end = instr.find("]")
        admin.append(instr[:end + 1])
        instr = instr[end + 1:].strip()
    return " ".join(admin), instr


norm = lambda s: re.sub(r"\s+", " ", (s or "")).strip().lower()


##### === 1. D31 STATED DATES === #####
sch = load_json(os.path.join(D31, "schema.json"))
items = load_json(os.path.join(D31, "items.json"))
want = {str(i["eventid"]) for i in items if i["variant"] == "stated"}


def load_ev(fn):
    ev = {}
    for line in open(os.path.join(SCRATCH, fn), encoding="utf-8"):
        m = re.match(r'\{"eventid": (\d+)', line)
        if m and m.group(1) in want:
            ev[m.group(1)] = json.loads(line)
    return ev


ev_cur = load_ev("event_evidence.jsonl")
ev_old = load_ev("event_evidence.pre_d69_20260929.jsonl")   # the extraction ran 2026-06-12, before the D-69 rebuild

n_found = 0
for it in items:
    if it["variant"] == "adjudicate":
        # JUDGMENT: the quote/summary come from the extractor, i.e. one of the two candidates; showing
        # them tells the coder which side is which. Kept in the item under new names, not displayed.
        it["extractor_quote_hidden"] = it.pop("date_evidence_quote", None)
        it["extractor_summary_hidden"] = it.pop("extract_summary", None)
        continue
    e = str(it["eventid"])
    q = it.get("date_evidence_quote") or ""
    pieces = [norm(p) for p in re.split(r"\.\.\.|…", q) if len(norm(p)) >= 20] or [norm(q)]
    hit = None
    for ev in (ev_cur, ev_old):
        for x in (ev.get(e) or {}).get("items", []):
            raw = (x.get("snippet") or "")
            text = norm(raw)
            if all(p in text for p in pieces):
                hit = (x, raw, None)
                break
        if hit:
            break
    if not hit:
        # fallback: longest common substring >= 40 chars (quotes reordered around a dateline)
        best = None
        for ev in (ev_cur, ev_old):
            for x in (ev.get(e) or {}).get("items", []):
                raw = x.get("snippet") or ""
                sm = SequenceMatcher(None, q.lower(), raw.lower(), autojunk=False).find_longest_match(0, len(q), 0, len(raw))
                if not best or sm.size > best[0]:
                    best = (sm.size, x, raw, max(0, sm.b - sm.a))   # align the marker with the quote's start
        if best and best[0] >= 40:
            hit = (best[1], best[2], best[3])
    if hit:
        x, raw, pos = hit
        end = None
        if pos is None:
            # normalized text -> raw offsets (whitespace runs collapse to one space, leading space dropped)
            nchars, nmap = [], []
            for rx in range(len(raw)):
                ch = raw[rx]
                if ch.isspace():
                    if nchars and nchars[-1] != " ":
                        nchars.append(" "); nmap.append(rx)
                else:
                    nchars.append(ch.lower()); nmap.append(rx)
            ntext = "".join(nchars)
            p0 = ntext.find(pieces[0])
            p1 = ntext.find(pieces[-1], max(p0, 0))
            if p0 >= 0 and p1 >= 0:
                pos = nmap[p0]
                end = nmap[p1 + len(pieces[-1]) - 1] + 1
            else:
                pos = max(raw.lower().find(max(pieces, key=len)[:30]), 0)
        if end is None:
            end = min(len(raw), pos + len(q))
        lo, hi = max(0, pos - 350), min(len(raw), end + 350)
        window = ("…" if lo > 0 else "") + raw[lo:pos] + "⟦" + raw[pos:end] + "⟧" + raw[end:hi] + ("…" if hi < len(raw) else "")
        # corpus artefact: newlines stored as a bare Latin "n" between Cyrillic/punctuation
        window = re.sub(r'(?<=[а-яёА-ЯЁ.,;:!?»")])n(?=[А-ЯЁа-яё«"(])', " ", window)
        head = "[%s · %s%s]" % (x.get("date") or "?", x.get("src") or "?",
                                (" · " + x["channel"]) if x.get("channel") and x.get("channel") != "None" else "")
        title = (x.get("title") or "")
        title = "" if title in ("None", "nan") else title
        it["source_item"] = head + (" " + title if title else "") + "\n" + window
        url = x.get("url") or ""
        it["source_url"] = url if str(url).startswith("http") else None
        n_found += 1
    else:
        it["source_item"] = "(the news item this sentence came from could not be found in the evidence file — use the search links)"
        it["source_url"] = None
print("D31: source item located for", n_found, "of", len(want), "stated cards")
assert n_found >= 31

admin, rest = split_admin(sch["instructions"])
sch["admin_note"] = admin
sch["instructions"] = rest
for v in list(sch.get("instructions_by_variant", {})):
    sch["instructions_by_variant"][v] = split_admin(sch["instructions_by_variant"][v])[1]
sch["start_by_variant"] = {
    "stated": (
        "WHAT YOU SEE: one accident or disaster from the FPP digest, and the date a model pulled out of news "
        "coverage of it (yellow), with the sentence it took the date from.\n"
        "'Where the sentence comes from' is the news item that sentence sits in, the sentence marked ⟦…⟧. "
        "If no item could be found it says so; use the search links.\n"
        "THE QUESTION: is the yellow date the day the event itself happened (the first day, if it lasted "
        "several)? Not a court date, inspection, anniversary or publication date.\n"
        "YES = that exact day. NO = a different day: type the true date, as exactly as you can. "
        "UNSURE = the card plus a quick search don't settle it.\n"
        "Search only if the card doesn't settle it."),
    "adjudicate": (
        "WHAT YOU SEE: one incident and two candidate dates, A and B, from two different sources. You are "
        "not told which source is which.\n"
        "THE QUESTION: which is the day the incident itself happened (the first day, if it lasted several)? "
        "If both are wrong: 'Neither' and type the true date. Search as needed."),
}
new_display = []
for d in sch["display"]:
    if d["field"] == "evidence_snippets":
        continue
    if d["field"] == "date_evidence_quote":
        d["label"] = "Sentence the model took the date from"
    if d["field"] == "extract_summary":
        d["label"] = "Model's summary of its sources"
        new_display.append(d)
        new_display.append({"field": "source_item", "label": "Where the sentence comes from (news item, sentence marked ⟦…⟧)", "format": "longtext"})
        new_display.append({"field": "source_url", "label": "source article", "format": "link"})
        continue
    new_display.append(d)
sch["display"] = new_display
sch["reset_answers"] = {"before": RESET_BEFORE, "items": D31_RESET,
                        "why": "IPAD1028-D2 a (6 unsure, snippets unrelated) + d31k_81564 (quote named the extractor side); shown fresh once"}
save_json(sch, os.path.join(D31, "schema.json"))
save_json(items, os.path.join(D31, "items.json"))


##### === 2. CASE LINKAGE S1 === #####
sch = load_json(os.path.join(CLP, "schema.json"))
items = load_json(os.path.join(CLP, "items.json"))
key = {r["item_id"]: r for r in csv.DictReader(open(CLP_KEY, encoding="utf-8"))}
need = json.load(open(os.path.join(SCRATCH, "need_ids.json"), encoding="utf-8"))
tg = json.load(open(os.path.join(SCRATCH, "tg_found.json"), encoding="utf-8"))
sh = {}
for row in csv.DictReader(open(os.path.join(SCRATCH, "rusmedia_arrest_articles.csv"), encoding="utf-8")):
    u = row.get("url", "")
    sid = "sh_%s_%s" % (row.get("portal", ""), u.split("/")[-2] if "/" in u else "")
    sh[sid] = row
sid_of = {(n[0], n[1]): n[2] for n in need}

n_ext, n_link = 0, 0
for it in items:
    for slot in ["a", "b1", "b2", "b3"]:
        if not it.get(slot + "_text"):
            continue
        sid = B_SID_OVERRIDE.get((it["item_id"], slot)) or sid_of.get((it["item_id"], slot[0] if slot == "a" else slot))
        if not sid:
            continue
        if sid.startswith("tg_") and sid in tg:
            r = tg[sid]
            full = r["text"].strip()
            if len(full) > len(it[slot + "_text"].rstrip(".").rstrip()):
                it[slot + "_text"] = full + (" […first 500 characters; open the original for the rest]" if len(full) >= 500 else "")
                n_ext += 1
            it[slot + "_url"] = "https://t.me/%s/%s" % (r["channel"], r["message_id"])
            n_link += 1
        elif sid.startswith("sh_") and sid in sh:
            u = sh[sid].get("url", "")
            if u.startswith("http"):
                it[slot + "_url"] = u
                n_link += 1
    for slot in ["a", "b1", "b2", "b3"]:
        if it.get(slot + "_text"):
            it[slot + "_text"] = it[slot + "_text"].replace("**", "")
print("case linkage: texts extended", n_ext, "; original links added", n_link)

admin, rest = split_admin(sch["instructions"])
sch["admin_note"] = admin
sch["instructions"] = rest
sch["start"] = (
    "WHAT YOU SEE: A is a news mention of an official being detained, charged or tried. Most of these cards "
    "show no B — that is expected, not an error. Where B1–B3 appear, they are earlier mentions from the "
    "same region.\n"
    "Q1 (every card): from A, is this the FIRST public news of the case (detention, case opened, caught in "
    "the act) or a FOLLOW-UP to a case already public (charges filed, court ordered or extended arrest, "
    "trial, verdict, «ранее задержанный», «фигурант дела»)? 'Can't tell' is a real answer — use it "
    "whenever A doesn't say.\n"
    "Q2 (only if a B is shown): is A the same criminal case as B1, B2 or B3? Pick the first that is.\n"
    "'Open the original' shows the full post or article (regional-media cards show only a headline "
    "otherwise). The model that made this call saw only the first 250 characters or the headline. "
    "Judge from A and its original; no other searching.")
new_display = []
for d in sch["display"]:
    new_display.append(d)
    m = re.match(r"^(a|b\d)_text$", d["field"])
    if m:
        new_display.append({"field": m.group(1) + "_url", "label": m.group(1).upper() + " — open the original", "format": "link"})
sch["display"] = new_display
sch["reset_answers"] = {"before": RESET_BEFORE, "items": CLP_RESET, "why": "answered on the old 250-char card; shown fresh once"}
save_json(sch, os.path.join(CLP, "schema.json"))
save_json(items, os.path.join(CLP, "items.json"))


##### === 3. ELVIS === #####
sch = load_json(os.path.join(ELV, "schema.json"))
items = load_json(os.path.join(ELV, "items.json"))
CITY_RU = {"Ekaterinburg": "Екатеринбург", "Kazan'": "Казань", "Nizhnekamsk": "Нижнекамск", "Tomsk": "Томск",
           "Syktyvkar": "Сыктывкар", "Nizhnij Tagil": "Нижний Тагил", "Novoural'sk": "Новоуральск",
           "Jelista": "Элиста", "Kamensk-Ural'skij": "Каменск-Уральский"}
LEVEL_RU = {"mayor": "глава города (мэр)", "governor": "глава региона", "duma_deputy": "депутат Госдумы",
            "vice_governor": "вице-губернатор / зампред правительства", "body_head": "руководитель регионального ведомства",
            "regional_minister": "региональный министр", "regional_legislator": "депутат регионального парламента"}
n_post = 0
for it in items:
    reg, lev = it["region_body"].split(" · уровень: ")
    it["region_body"] = "%s · %s" % (reg, LEVEL_RU.get(lev, lev))
    if lev == "mayor":
        if it["post"] in CITY_RU:
            it["post"] = "глава города (мэр): " + CITY_RU[it["post"]]
            n_post += 1
        elif it["post"] == "мэр":
            it["post"] = "глава города (мэр); город в базе не указан"
    # Telegram/VK markdown: bold/italic markers only, the matcher's ⟦…⟧ kept
    it["span"] = re.sub(r"\*\*|__", "", it["span"]).replace("⟦ ", " ⟦").replace("*⟧*", "⟧").replace("*⟧", "⟧")
assert all(not re.fullmatch(r"[A-Za-z' \-]+", i["post"]) for i in items), "a Latin-only post is left"
print("ELVIS: mayor posts fixed", n_post)

admin, rest = split_admin(sch["instructions"])
sch["admin_note"] = admin
sch["instructions"] = rest
sch["start"] = (
    "WHAT YOU SEE: a snippet from a news or social-media text. A name-matching program found a name in it "
    "(marked ⟦…⟧) and linked it to the official at the top, from our officials database: post, region, "
    "years in post.\n"
    "1. SAME PERSON? Is the marked name this official, not someone else with the same name?\n"
    "2. IN POST ON THAT DATE? On the publication date, did this person hold the post shown (or one close to "
    "it)? The database years are only accurate to the year. If the text shows they had already left or not "
    "yet started: no.\n"
    "3. ABOUT THEIR REGION? Is the mention about their role in their region, not another level or region?\n"
    "'Unsure' when the snippet isn't enough; the link opens the full text.")
for d in sch["display"]:
    if d["field"] == "region_body":
        d["label"] = "Регион / тип должности"
sch["reset_answers"] = {"before": RESET_BEFORE, "items": ELV_RESET, "why": "notes-only answer on the old card; shown fresh once"}
save_json(sch, os.path.join(ELV, "schema.json"))
save_json(items, os.path.join(ELV, "items.json"))


##### === PROVENANCE === #####
line = ("\n2026-10-28 IPAD1028-D1/D2/D3 = a (Noah): display-only rebuild by "
        "me/website/validation/build_2026-10-28_ipad1028_fixes.py; same items, order and ids; pre-fix copies *.pre_ipad1028. "
        "See _notes/ipad_feedback_2026-10-28.md.")
for d in (D31, CLP, ELV):
    pv = os.path.join(d, "items.json.provenance.txt")
    if line.strip() not in open(pv, encoding="utf-8").read():
        with open(pv, "a", encoding="utf-8") as fh:
            fh.write(line)
print("done")


