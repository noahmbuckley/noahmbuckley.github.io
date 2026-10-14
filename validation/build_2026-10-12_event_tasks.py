#!/usr/bin/env python3
"""Build the 2026-10-12 event-data iPad task set (EVIV session; see _notes/event_iv_review_2026-10-12.md §6).

Idempotent. Reads staged sets (read-only) and writes ONLY under me/website/validation/:
  data/<new-task>/{items.json,schema.json,items.json.provenance.txt}, tasks.json, tasks_retired_2026-10-12.json, sw.js (VERSION).
Never opens any KEY / sealed / referee file. The protest dedup block map is taken from items_key.csv by reading
two columns only (item_id, block); no answer column is read into memory beyond that row dict's discard.
"""
import csv, json, os, re, hashlib, datetime, shutil, sys

ROOT = '/Users/noahbuckley/Dropbox/Projects'
V = os.path.join(ROOT, 'me/website/validation')
D = os.path.join(V, 'data')
TODAY = '2026-10-12'

def load_items(p):
    it = json.load(open(p))
    if isinstance(it, dict):
        it = it.get('items', it)
    return it

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

def write_task(task_id, items, schema, provenance_lines, name_suffix=None, instr_prefix=None):
    out = os.path.join(D, task_id)
    os.makedirs(out, exist_ok=True)
    sch = json.loads(json.dumps(schema))
    sch['task_id'] = task_id
    if name_suffix:
        sch['name'] = name_suffix
    if instr_prefix:
        sch['instructions'] = instr_prefix + ' ' + (sch.get('instructions') or '')
        # the app shows instructions_by_variant INSTEAD of instructions when the item has a variant
        for k in list((sch.get('instructions_by_variant') or {}).keys()):
            sch['instructions_by_variant'][k] = instr_prefix + ' ' + (sch['instructions_by_variant'][k] or '')
    json.dump(items, open(os.path.join(out, 'items.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(sch, open(os.path.join(out, 'schema.json'), 'w'), ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'items.json.provenance.txt'), 'w') as f:
        f.write(f'built {datetime.datetime.now().isoformat(timespec="seconds")} by build_2026-10-12_event_tasks.py\n')
        f.write(f'n_items {len(items)}\n')
        for l in provenance_lines:
            f.write(l + '\n')
    print(f'  wrote {task_id}: {len(items)} items')
    return len(items)

tasks = []

# ---------- 1. Disaster D-31 stated dates, referee-reduced subset (23) ----------
src = os.path.join(ROOT, 'disaster/validation/D31_stated_date_stage_v3_2026-10-04')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
sub = [r['item_id'] for r in csv.DictReader(open(os.path.join(src, 'human_subset_2026-10-12.csv')))]
keep = [x for x in items if x['item_id'] in set(sub)]
assert len(keep) == len(sub) == 23, (len(keep), len(sub))
n = write_task('disaster-D31-stated-date-subset23', keep, schema,
    [f'source items {src}/items.json md5 {md5(os.path.join(src,"items.json"))}',
     f'filter: human_subset_2026-10-12.csv (REF1012 referee pass; disagreements + unclear + seeded 20% of agreements)'],
    name_suffix='Disaster D-31 stated dates — 23-card human subset (REF1012)',
    instr_prefix='[2026-10-12 SUBSET: code ALL 23 cards in one pass; the round/stop-rule sentence below no longer applies — the other 59 cards were pre-coded by two referees and are scored as audited silver.]')
tasks.append({
  'id': 'disaster-D31-stated-date-subset23',
  'name': f'1 · Disaster D-31 stated dates — human subset (23, ~28 min)',
  'project': 'disaster',
  'description': 'DO FIRST. Referee-reduced subset (REF1012, 10-12) of the v3 stated-date gate: tolerance ±3 d, bar 0.70 (DIS1004-D10). Gates day precision for 1,756 events (talk 10-17). Blind; search only if the card does not settle it. Loader disaster/code/validation/99d3_load_date_validation_v3_results.R (subset+silver amendment pending, EVIV-D6).',
  'schema_url': 'data/disaster-D31-stated-date-subset23/schema.json',
  'items_url': 'data/disaster-D31-stated-date-subset23/items.json'})

# ---------- 2. Protest dedup gold, blocks H1 + H2 + D in full (54) ----------
src = os.path.join(ROOT, 'eventsData/protestData/validation/dedup_gold_stage_2026-10-04')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
block = {}
with open(os.path.join(src, 'items_key.csv')) as f:
    for r in csv.DictReader(f):
        block[r['item_id']] = r['block']   # only these two columns are retained
A = {'H1_cg_only', 'H2_v2_only', 'D_date'}
B = {'RS_reasons', 'B1_cg_struct', 'B2_kk_boundary', 'B3_kprime', 'B4_cross_lowcos', 'B5_silver_check'}
keepA = [x for x in items if block.get(x['item_id']) in A]
keepB = [x for x in items if block.get(x['item_id']) in B]
assert len(keepA) == 54 and len(keepB) == 63, (len(keepA), len(keepB))
# keep original seq order (interleaved); cards are blind to block
prov = [f'source items {src}/items.json md5 {md5(os.path.join(src,"items.json"))}',
        'filter: items_key.csv column block only (no answer columns read)']
write_task('protest-dedup-gold-A-H1H2D', keepA, schema, prov + ['blocks H1_cg_only (15) + H2_v2_only (15) + D_date (24); full blocks so the per-block SPRT/majority rules (DESIGN_NOTES) run intact'],
    name_suffix='Protest dedup gold — part A (H1/H2 head-to-head + article dates), 54 cards',
    instr_prefix='[Part A of the 10-04 gold: 30 pair cards + 24 article-date cards, full blocks.]')
write_task('protest-dedup-gold-B-rules', keepB, schema, prov + ['blocks RS (12) + B1 (10) + B2 (15) + B3 (10) + B4 (6) + B5 (10)'],
    name_suffix='Protest dedup gold — part B (rule boundaries + silver check), 63 cards',
    instr_prefix='[Part B of the 10-04 gold: 63 pair cards, full blocks.]')
tasks.append({
  'id': 'protest-dedup-gold-A-H1H2D',
  'name': '1 · Protest dedup gold A — same event? + article dates (54, ~30 min)',
  'project': 'eventsData/protestData',
  'description': 'DO SECOND. Decides the protests IV: PROTWL-D1 (content-gated rule vs fastLink as primary linkage) and PRV2-D4 (Kasparov vs namarsh date). Blind pair cards (30) + article-date cards (24), coded as full blocks so the pre-declared per-block rules fire. Loader eventsData/protestData/upd/T9_content_rule/03_load_gold_answers.R. Memo eventsData/protestData/notes/weaklink_dedup_completeness_2026-10-04.md.',
  'schema_url': 'data/protest-dedup-gold-A-H1H2D/schema.json',
  'items_url': 'data/protest-dedup-gold-A-H1H2D/items.json'})

# ---------- 3. Disaster event REALITY block (31) from the response session ----------
src = os.path.join(D, 'disaster-response-session')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
keep = [x for x in items if 'reality' in str(x.get('variant', ''))]
assert len(keep) == 31, len(keep)
write_task('disaster-event-reality-31', keep, schema,
    [f'source items {src}/items.json md5 {md5(os.path.join(src,"items.json"))}', 'filter: variant contains "reality" (29 reality + kremlin+reality + decree+reality)'],
    name_suffix='Disaster event reality — 31 cards (did this event happen as described?)',
    instr_prefix='[2026-10-12: only the EVENT-REALITY block of the 10-04 response session; the response blocks are frozen (EVIV review). Ignore the round/loader sentence below. Two cards also carry a second document question; answer it if shown.]')
tasks.append({
  'id': 'disaster-event-reality-31',
  'name': '1 · Disaster event reality — candidate non-events (31, ~9 min)',
  'project': 'disaster',
  'description': 'DO THIRD. The REALITY block only: 20 candidate non-events (N 12 + C 8) + 11 calibration cards, blind. Informs how Table 1\'s weakly-confirmed slice (A7) is read and DIS1004-D1 (clean the universe). The response blocks (Kremlin, decree, Track A) are frozen until the framing call. Loader disaster/code/validation/99m_load_response_session_results.R.',
  'schema_url': 'data/disaster-event-reality-31/schema.json',
  'items_url': 'data/disaster-event-reality-31/items.json'})

# ---------- 4. Protest validation residue, article cards only (23) ----------
src = os.path.join(D, 'protest-validation-residue')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
keep = [x for x in items if str(x.get('variant', '')).startswith('article')]
assert len(keep) == 23, len(keep)
write_task('protest-validation-residue-articles23', keep, schema,
    [f'source items {src}/items.json md5 {md5(os.path.join(src,"items.json"))}', 'filter: variant in article_protest / article_date / article_region (the 17 pair cards dropped: 11 have no text on one side)'],
    name_suffix='Protest validation residue — article cards (23)',
    instr_prefix='[2026-10-12: article cards only (real protest? / date / region); the 17 pair cards were dropped as mostly unanswerable.]')
tasks.append({
  'id': 'protest-validation-residue-articles23',
  'name': '1 · Protest residue — real protest? / date / region (23, ~12 min)',
  'project': 'eventsData/protestData',
  'description': 'DO FOURTH (if time). Human tier for the Kasparov precision / recall / date / region silver numbers (pkg_2026-09-28/SUMMARY.md). No gate; measurement only. Loader eventsData/protestData/code/validation/61_load_residue_answers.R.',
  'schema_url': 'data/protest-validation-residue-articles23/schema.json',
  'items_url': 'data/protest-validation-residue-articles23/items.json'})

# ---------- 5. Arrests case linkage, referee subset (74) ----------
src = os.path.join(ROOT, 'arrestsPubOpinionPaper/validation/case_linkage_pairs_stage_2026-10-04')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
sub = [r['item_id'] for r in csv.DictReader(open(os.path.join(src, 'human_subset_2026-10-12.csv')))]
keep = [x for x in items if x['item_id'] in set(sub)]
assert len(keep) == len(sub) == 74
write_task('arrests-case-linkage-subset74', keep, schema,
    [f'source items {src}/items.json md5 {md5(os.path.join(src,"items.json"))}', 'filter: human_subset_2026-10-12.csv (REF1012)'],
    name_suffix='Arrests case linkage — 74-card human subset (REF1012)',
    instr_prefix='[2026-10-12 SUBSET: code all 74; the round sentence below no longer applies — the other 86 cards were pre-coded by two referees (audited silver).]')
tasks.append({
  'id': 'arrests-case-linkage-subset74',
  'name': '2 · Arrests case linkage — same criminal case? (74, ~30 min)',
  'project': 'arrestsPubOpinionPaper',
  'description': 'NEXT SITTING. Referee-reduced subset of the 10-04 "same case?" cards. Decides ARRWL-D1/D2 (adopt the linker fixes) and feeds the first-case rule. Blind. Loader arrestsPubOpinionPaper/code/load_case_linkage_pairs_results_2026-10-04.R (subset amendment pending, EVIV-D6). Memo notes/weaklink_case_linkage_2026-10-04.md.',
  'schema_url': 'data/arrests-case-linkage-subset74/schema.json',
  'items_url': 'data/arrests-case-linkage-subset74/items.json'})

# ---------- 6. Protest dedup part B (registered above) ----------
tasks.append({
  'id': 'protest-dedup-gold-B-rules',
  'name': '2 · Protest dedup gold B — rule boundaries + silver check (63, ~32 min)',
  'project': 'eventsData/protestData',
  'description': 'NEXT SITTING. Blocks RS/B1–B5 of the 10-04 gold: sets the content-gated rule\'s thresholds (TAU_WITHIN), must-link ON/OFF (PRV2-D5) and the silver-trust check. Same loader as part A.',
  'schema_url': 'data/protest-dedup-gold-B-rules/schema.json',
  'items_url': 'data/protest-dedup-gold-B-rules/items.json'})

# ---------- 7. Arrests crime-type audit, referee subset (35) — converted from csv ----------
src_csv = os.path.join(ROOT, 'arrestsPubOpinionPaper/validation/reclass_audit_sample_2026-07-21.csv')
sub = [r['item_id'] for r in csv.DictReader(open(os.path.join(ROOT, 'arrestsPubOpinionPaper/validation/reclass_audit_referee_2026-10-12/human_subset_2026-10-12.csv')))]
rows = list(csv.DictReader(open(src_csv, encoding='utf-8')))
keep = [{'item_id': r['row_id'], 'card_label': r['row_id'], 'date': r['date'], 'region': r['region'],
         'official_desc': r['official_desc'], 'event_text': r['event_text']} for r in rows if r['row_id'] in set(sub)]
assert len(keep) == len(sub) == 35
labels = [('bribery', 'bribery — взятка / подкуп', '1'), ('abuse_of_office', 'abuse_of_office — превышение / злоупотребление', '2'),
          ('embezzlement', 'embezzlement — присвоение / растрата', '3'), ('fraud', 'fraud — мошенничество', '4'),
          ('tax_evasion', 'tax_evasion — уклонение от налогов', '5'), ('extortion', 'extortion — вымогательство', '6'),
          ('corruption', 'corruption — generic, no offence named', '7'), ('not_criminal', 'not_criminal — no criminal matter', '8'),
          ('unknown', 'unknown — cannot tell from the text', '9')]
schema = {
  'task_id': 'arrests-crime-type-subset35', 'name': 'Arrests crime-type audit — 35-card human subset (REF1012)', 'version': 'v1 2026-10-12',
  'id_field': 'item_id', 'hide_empty': True,
  'instructions': "[2026-10-12 SUBSET of the 125-event audit (validation/START_HERE.md); 90 cards were pre-coded by two referees.] Read the Russian event text and pick ONE crime-type label from the classifier's own vocabulary. Judge the OFFENCE named in the text, not the official's rank. 'corruption' only when the text says corruption without naming an offence. Use 'unknown' freely: a forced guess is worse than a missing label. No model label is shown.",
  'display': [
    {'field': 'date', 'label': 'Month', 'format': 'compact'},
    {'field': 'region', 'label': 'Region', 'format': 'compact'},
    {'field': 'official_desc', 'label': 'Official', 'format': 'compact'},
    {'field': 'event_text', 'label': 'Event text (code from this)', 'format': 'longtext'}],
  'validation': [
    {'field': 'noah_code', 'label': 'Crime type', 'required': True, 'type': 'enum',
     'options': [{'value': v, 'label': l, 'key': k, 'tone': ('warn' if v in ('unknown', 'corruption') else 'neutral')} for v, l, k in labels]},
    {'field': 'notes', 'label': 'Notes', 'required': False, 'type': 'text', 'placeholder': 'optional'}]}
write_task('arrests-crime-type-subset35', keep, schema,
    [f'source {src_csv} md5 {md5(src_csv)}', 'filter: reclass_audit_referee_2026-10-12/human_subset_2026-10-12.csv (row_id)', 'labels from validation/START_HERE.md §2'])
tasks.append({
  'id': 'arrests-crime-type-subset35',
  'name': '2 · Arrests crime type — bribery vs other (35, ~20 min)',
  'project': 'arrestsPubOpinionPaper',
  'description': 'NEXT SITTING. Referee-reduced subset of the 125-event crime-type audit (did the 46-category classifier over-split bribery?). Also the gold rusclf arrest_extract needs. Scorer code/89_score_reclass_audit.R must be amended to accept the subset (EVIV-D6).',
  'schema_url': 'data/arrests-crime-type-subset35/schema.json',
  'items_url': 'data/arrests-crime-type-subset35/items.json'})

# ---------- 8. Disaster adjacent pairs, same incident? (80) — built by disaster/code/validation/99p_* ----------
src = os.path.join(ROOT, 'disaster/validation/adjacent_pairs_stage_2026-10-12')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
assert len(items) == 80
write_task('disaster-adjacent-pairs-80', items, schema,
    [f'source {src}/items.json md5 {md5(os.path.join(src,"items.json"))}', 'all 80 pairs; blind; key in the stage dir'])
tasks.insert(4, {
  'id': 'disaster-adjacent-pairs-80',
  'name': '1b · Disaster adjacent pairs — same incident? (80, ~25 min)',
  'project': 'disaster',
  'description': 'PULL FORWARD IF TIME. 80 consecutive day-dated event pairs, same region + type, 0–3 days apart (62 same-day); the hygiene census catches 16 clusters. Measures double-counted exposure (aftermath / ЧС-decree rows as separate treated events). Pre-declared rule in disaster/validation/adjacent_pairs_stage_2026-10-12/README.md; loader TODO 99q_.',
  'schema_url': 'data/disaster-adjacent-pairs-80/schema.json',
  'items_url': 'data/disaster-adjacent-pairs-80/items.json'})

# ---------- 9. Sledcom defendant adjudication, BLIND rebuild (60) ----------
src = os.path.join(ROOT, 'arrestsPubOpinionPaper/validation/sledcom_defendant_blind_stage_2026-10-12')
items = load_items(os.path.join(src, 'items.json'))
schema = json.load(open(os.path.join(src, 'schema.json')))
assert len(items) == 60
write_task('arrests-sledcom-defendant-blind60', items, schema,
    [f'source {src}/items.json md5 {md5(os.path.join(src,"items.json"))}', 'blind rebuild of the 10-10 workbook (model columns removed); stratum in the sealed key'])
tasks.append({
  'id': 'arrests-sledcom-defendant-blind60',
  'name': '2 · Sledcom rows 2023–26 — is an official the defendant? (60, ~35 min)',
  'project': 'arrestsPubOpinionPaper',
  'description': 'NEXT SITTING. Blind rebuild of the 10-10 adjudication workbook (which showed the model\'s labels). Human anchor for the ~1,300 silver-driven Sledcom deletions (ARR1010-D3) and the open 162-row list (EDA1012-D3). Rule in arrestsPubOpinionPaper/validation/sledcom_defendant_blind_stage_2026-10-12/README.md; loader TODO.',
  'schema_url': 'data/arrests-sledcom-defendant-blind60/schema.json',
  'items_url': 'data/arrests-sledcom-defendant-blind60/items.json'})

# ---------- campaign2026 tasks: carried over unchanged, below the event tasks ----------
old = json.load(open(os.path.join(V, 'tasks.json')))
c26 = [t for t in old['tasks'] if t['project'] == 'campaign2026']
for t in c26:
    t = dict(t)
    t['name'] = 'C26 · ' + re.sub(r'^(T1 · |C26 · )+', '', t['name'])   # 2026-10-14: idempotent (re-runs had stacked 'C26 · ' four times)
    tasks.append(t)

# ---------- retired entries ----------
retired_ids = ['disaster-D31-stated-date', 'disaster-response-session', 'protest-validation-residue']
retired = [t for t in old['tasks'] if t['id'] in retired_ids]
for t in retired:
    t['retired'] = TODAY
    t['retired_reason'] = {
      'disaster-D31-stated-date': 'replaced by disaster-D31-stated-date-subset23 (REF1012 referee pass); the 82-card data dir stays on disk',
      'disaster-response-session': 'response blocks frozen until the disaster framing call (EVIV review 2026-10-12); the REALITY block lives on as disaster-event-reality-31',
      'protest-validation-residue': 'replaced by protest-validation-residue-articles23; the 17 pair cards were dropped (11 unanswerable without text)'}[t['id']]
if retired:   # 2026-10-14: a re-run reads the already-rebuilt tasks.json, finds nothing to retire, and used to blank this file
    json.dump({'retired_on': TODAY, 'tasks': retired}, open(os.path.join(V, f'tasks_retired_{TODAY}.json'), 'w'), ensure_ascii=False, indent=2)

new = {'schema_version': 1, 'generated_at': TODAY, 'tasks': tasks}
json.dump(new, open(os.path.join(V, 'tasks.json'), 'w'), ensure_ascii=False, indent=2)
print('tasks.json:', [t['id'] for t in tasks])

# ---------- sw.js VERSION bump ----------
sw = open(os.path.join(V, 'sw.js')).read()
sw2 = re.sub(r"const VERSION = 'v\d+-\d{4}-\d{2}-\d{2}';", f"const VERSION = 'v17-{TODAY}';", sw)
assert sw2 != sw or f'v16-{TODAY}' in sw
open(os.path.join(V, 'sw.js'), 'w').write(sw2)
print('sw.js VERSION ->', re.search(r"const VERSION = '([^']+)'", sw2).group(1))
