#!/usr/bin/env python3
"""
build_samples.py — Build the JSON samples the viewer serves.

For each database (Telegram posts, VK posts, rusMedia articles), pull a
stratified random sample of ~N items, normalize to a common schema, and
write data/<db>.json. The viewer (index.html + app.js) is purely client-side
and loads these files at page load.

Designed to be re-run periodically (cron'able) to refresh the samples.

Schema per item:
  { id, db, date, source, title, text, url, regionid, metadata: {…} }

URLs are the verification handles:
  Telegram: https://t.me/{channel_username}/{message_id}
  VK:       https://vk.com/wall-{group_id}_{post_id}
  rusMedia: stored verbatim from the source CSV's 'url' column
"""
import json, os, glob, random, sys, traceback
from pathlib import Path

random.seed(20260526)
N_PER_DB    = 2000
MAX_TEXT    = 2000             # cap text per item — keeps JSON files lean
HERE        = Path(__file__).resolve().parent
DATA_DIR    = HERE / "data"
DATA_DIR.mkdir(exist_ok=True)

RS_POSTS = Path.home() / "Dropbox/Projects/rusSocial/data/processed/posts"
VK_POSTS = Path.home() / "Dropbox/Projects/rusSocial/vk/data/processed/posts"
RM_PROC  = Path.home() / "Dropbox/Projects/rusMedia/data/processed"


def truncate(s, n=MAX_TEXT):
    if s is None: return None
    s = str(s)
    return s if len(s) <= n else s[:n] + " …[truncated]"


def stratified_sample(parquet_paths, n_total, text_col, normalize_fn, file_label="file"):
    """Pick floor(n_total / k) random rows from each of min(k, len(paths)) parquets.
    k is auto: aim for ~30-40 items per file when sampling, capped by file count."""
    import pyarrow.parquet as pq
    if not parquet_paths:
        return []
    per_file_target = max(20, min(80, n_total // min(len(parquet_paths), 60)))
    # Pick a random subset of files if we have way more files than needed.
    n_files_to_use = min(len(parquet_paths), max(30, (n_total // per_file_target) * 2))
    use = random.sample(parquet_paths, n_files_to_use)
    out, errs = [], 0
    for p in use:
        if len(out) >= n_total: break
        try:
            tbl = pq.read_table(p)
            if tbl.num_rows == 0: continue
            idx = random.sample(range(tbl.num_rows), min(per_file_target, tbl.num_rows))
            sub = tbl.take(idx).to_pylist()
            for r in sub:
                if not r.get(text_col): continue
                item = normalize_fn(r, p)
                if item: out.append(item)
                if len(out) >= n_total: break
        except Exception as e:
            errs += 1
            if errs <= 3: print(f"  WARN {p.name}: {e}", file=sys.stderr)
    random.shuffle(out)
    return out[:n_total]


##### Telegram #####
def normalize_telegram(r, parquet_path):
    cu = r.get("channel_username") or parquet_path.stem
    mid = r.get("message_id")
    return {
        "id": f"tg_{cu}_{mid}",
        "db": "telegram",
        "date": str(r.get("date")) if r.get("date") else None,
        "source": f"@{cu}" if cu and not cu.isdigit() else f"[channel #{parquet_path.stem}]",
        "title": None,
        "text": truncate(r.get("text")),
        "url": (f"https://t.me/{cu}/{mid}"
                if cu and not cu.isdigit() and mid is not None else None),
        "regionid": None,
        "metadata": {
            "views": r.get("views"),
            "forwards": r.get("forwards"),
            "comment_count": r.get("comment_count"),
            "media_type": r.get("media_type"),
        },
    }


def build_telegram():
    paths = sorted(RS_POSTS.glob("*.parquet"))
    print(f"telegram: {len(paths)} channel parquets")
    items = stratified_sample(paths, N_PER_DB, text_col="text",
                              normalize_fn=normalize_telegram, file_label="channel")
    print(f"  -> {len(items)} items")
    return items


##### VK #####
def normalize_vk(r, parquet_path):
    gid = r.get("group_id")
    pid = r.get("post_id")
    return {
        "id": f"vk_{gid}_{pid}",
        "db": "vk",
        "date": r.get("date_str") or (str(r.get("date")) if r.get("date") else None),
        "source": f"vk.com/club{gid}" if gid else f"[group {parquet_path.stem}]",
        "title": None,
        "text": truncate(r.get("text")),
        "url": (f"https://vk.com/wall-{gid}_{pid}"
                if gid is not None and pid is not None else None),
        "regionid": None,
        "metadata": {
            "views": r.get("views"),
            "likes": r.get("likes"),
            "comments_count": r.get("comments_count"),
            "reposts": r.get("reposts"),
            "post_type": r.get("post_type"),
        },
    }


def build_vk():
    paths = sorted(VK_POSTS.glob("*.parquet"))
    print(f"vk: {len(paths)} group parquets")
    items = stratified_sample(paths, N_PER_DB, text_col="text",
                              normalize_fn=normalize_vk, file_label="group")
    print(f"  -> {len(items)} items")
    return items


##### rusMedia #####
# rusMedia has three kinds of fulltext stores. All share the schema
# (url, pub_date, title, full_text, word_count[, regionid, section, …]),
# so one normalizer handles them all:
#
#   1) `national/corpus/` hive-partitioned parquet (20 outlets: kommersant,
#      lenta, ria, rt, vedomosti, gazeta, interfax, mkru_national, rg, ria, …)
#   2) Single-CSV outlets that aren't in national/corpus (regnum, fedpress,
#      izvestia, ng_wayback, rg_wayback, vedomosti_wayback, smotrim, rbc_national)
#   3) Regional outlet groups — directories where each CSV is a per-region slice
#      of one outlet (aif/kp/mkru/rbc regional papers). All slices roll up
#      under a single source label like `aif_regional`.
#   4) `filtered_fulltext/` — each CSV is its own regional portal (e.g.
#      116.ru = Kazan, e1.ru = Yekaterinburg, fontanka.ru = SPb). Treat each
#      as its own source so the dropdown reflects portal diversity.

RM_NATIONAL = RM_PROC / "national" / "corpus"

RM_SINGLE_CSVS = [
    # (path, source_label) — one CSV per outlet
    (RM_PROC / "rbc_national" / "rbc_fulltext.csv",          "rbc_national"),
    (RM_PROC / "izvestia"     / "izvestia_fulltext.csv",     "izvestia"),
    (RM_PROC / "regnum"           / "regnum_fulltext_clean.csv", "regnum"),
    (RM_PROC / "fedpress"         / "fedpress_fulltext.csv",     "fedpress"),
    (RM_PROC / "ng_wayback"       / "ng_fulltext.csv",           "ng_wayback"),
    (RM_PROC / "rg_wayback"       / "rg_fulltext.csv",           "rg_wayback"),
    (RM_PROC / "vedomosti_wayback"/ "vedomosti_fulltext.csv",    "vedomosti_wayback"),
    (RM_PROC / "smotrim"          / "smotrim_fulltext.csv",      "smotrim"),
    (RM_PROC / "commoncrawl"      / "cc_mkru_fulltext.csv",      "commoncrawl_mkru"),
]

RM_REGIONAL_GROUPS = [
    # (glob relative to RM_PROC, source_label) — sweep all CSVs, label uniformly
    ("aif_fulltext/aif_*.csv",      "aif_regional"),
    ("kp_fulltext/kp_*.csv",        "kp_regional"),
    ("mkru_fulltext/mkru_*.csv",    "mkru_regional"),
    ("rbc_fulltext/rbc_*.csv",      "rbc_regional"),
]

# Per-portal regional sites (filtered_fulltext/) — each CSV is a different
# regional outlet. Source label derived from filename.
RM_FILTERED_PORTALS_GLOB = "filtered_fulltext/*.csv"


def normalize_rusmedia_row(row, source_name):
    """row is a dict from either a parquet (national/corpus) or a fulltext CSV.
       Both layouts share url + title + full_text + pub_date + word_count fields."""
    txt = row.get("full_text") or row.get("text")
    if not txt: return None
    url = row.get("url")
    return {
        "id": f"rm_{source_name}_{row.get('url_id') or hash(str(url) or txt[:60]) & 0xffffffff}",
        "db": "rusmedia",
        "date": str(row.get("pub_date")) if row.get("pub_date") else None,
        "source": str(source_name),
        "title": row.get("title"),
        "text": truncate(txt),
        "url": url if url else None,
        "regionid": None,
        "metadata": {
            "word_count": row.get("word_count"),
            "section": row.get("section"),
            "year_month": row.get("year_month"),
        },
    }


def _reservoir_sample_csv(csv_path, target_n, csvmod):
    """Stream a CSV and return a uniform reservoir-sample of target_n dicts.
    Memory: O(target_n) regardless of file size. Safe for multi-GB CSVs."""
    reservoir = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        rdr = csvmod.DictReader(f)
        for i, row in enumerate(rdr):
            if i < target_n:
                reservoir.append(row)
            else:
                j = random.randint(0, i)
                if j < target_n:
                    reservoir[j] = row
    return reservoir


def build_rusmedia():
    import pyarrow.parquet as pq
    import csv as csvmod
    csvmod.field_size_limit(sys.maxsize)
    out = []

    # --- 1) national/corpus hive-partitioned parquets ---
    if RM_NATIONAL.exists():
        sources = sorted(p for p in RM_NATIONAL.glob("source=*") if p.is_dir())
        print(f"rusmedia/national: {len(sources)} sources")
        per_source = max(50, N_PER_DB // max(1, len(sources)))    # ~100 per source
        for sdir in sources:
            sname = sdir.name.replace("source=", "")
            parquets = list(sdir.rglob("*.parquet"))
            if not parquets: continue
            # pick 2-3 random parquets per source so we sweep across year_months
            picks = random.sample(parquets, min(3, len(parquets)))
            taken = 0
            for p in picks:
                if taken >= per_source: break
                try:
                    tbl = pq.read_table(p)
                    if tbl.num_rows == 0: continue
                    idx = random.sample(range(tbl.num_rows),
                                        min(per_source - taken, tbl.num_rows))
                    rows = tbl.take(idx).to_pylist()
                    for r in rows:
                        item = normalize_rusmedia_row(r, sname)
                        if item: out.append(item); taken += 1
                except Exception as e:
                    print(f"  WARN {p.name}: {e}", file=sys.stderr)

    # --- 2) single-CSV outlets (regnum, fedpress, ng_wayback, …) ---
    # RAM-safe streaming reservoir sample. Source labels are pre-set per CSV.
    SINGLE_TARGET = 100
    print(f"rusmedia/single: {len(RM_SINGLE_CSVS)} outlets")
    for csv_path, sname in RM_SINGLE_CSVS:
        if not csv_path.exists():
            print(f"  MISS {sname}: {csv_path}", file=sys.stderr); continue
        try:
            rows = _reservoir_sample_csv(csv_path, SINGLE_TARGET, csvmod)
            kept = 0
            for r in rows:
                item = normalize_rusmedia_row(r, sname)
                if item: out.append(item); kept += 1
            print(f"  {sname}: {kept}/{len(rows)} items")
        except Exception as e:
            print(f"  WARN {csv_path.name}: {e}", file=sys.stderr)

    # --- 3) regional outlet groups (aif/kp/mkru/rbc per-region CSVs) ---
    # Sweep all per-region CSVs in a group, reservoir-sample a small N per file,
    # roll up under one source label per group. Gives breadth-of-region within
    # one outlet while keeping dropdown clean.
    print(f"rusmedia/regional-groups: {len(RM_REGIONAL_GROUPS)} groups")
    for glob_rel, sname in RM_REGIONAL_GROUPS:
        files = sorted(RM_PROC.glob(glob_rel))
        if not files:
            print(f"  MISS {sname}: glob {glob_rel}", file=sys.stderr); continue
        # ~120 items per group spread across files
        per_file = max(2, 120 // len(files))
        kept = 0
        for fp in files:
            try:
                rows = _reservoir_sample_csv(fp, per_file, csvmod)
                for r in rows:
                    item = normalize_rusmedia_row(r, sname)
                    if item: out.append(item); kept += 1
            except Exception as e:
                print(f"  WARN {fp.name}: {e}", file=sys.stderr)
        print(f"  {sname}: {kept} items across {len(files)} regional CSVs (~{per_file}/file)")

    # --- 4) filtered_fulltext/ — each CSV is its own regional portal ---
    # Source label = filename stem with `_fulltext` stripped (e.g. "116_ru",
    # "fontanka_ru", "e1_ru"). Surfaces ~30 distinct regional outlets in the
    # dropdown.
    filtered_files = sorted(RM_PROC.glob(RM_FILTERED_PORTALS_GLOB))
    print(f"rusmedia/filtered_fulltext: {len(filtered_files)} portals")
    PORTAL_TARGET = 50
    for fp in filtered_files:
        sname = "ff_" + fp.stem.replace("_fulltext", "")
        try:
            rows = _reservoir_sample_csv(fp, PORTAL_TARGET, csvmod)
            for r in rows:
                item = normalize_rusmedia_row(r, sname)
                if item: out.append(item)
        except Exception as e:
            print(f"  WARN {fp.name}: {e}", file=sys.stderr)

    random.shuffle(out)
    print(f"  -> {len(out)} candidates; trimming to {min(N_PER_DB, len(out))}")
    return out[:N_PER_DB]


##### main #####
def main():
    builders = [("telegram", build_telegram),
                ("vk",       build_vk),
                ("rusmedia", build_rusmedia)]
    summary = {}
    for name, fn in builders:
        print(f"\n=== {name} ===")
        try:
            items = fn()
        except Exception:
            traceback.print_exc(); items = []
        out_path = DATA_DIR / f"{name}.json"
        # Also collect distinct sources for the UI dropdown
        sources = sorted(set(it.get("source") for it in items if it.get("source")))
        payload = {
            "db": name,
            "built_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "n_items": len(items),
            "n_sources": len(sources),
            "sources": sources,
            "items": items,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False))
        size_kb = out_path.stat().st_size / 1024
        summary[name] = (len(items), len(sources), int(size_kb))
        print(f"  wrote {out_path}  ({size_kb:.0f} KB)")

    print("\n=== summary ===")
    for k, (n, s, kb) in summary.items():
        print(f"  {k:10s}  items={n:>5}  sources={s:>5}  size={kb:>5} KB")


if __name__ == "__main__":
    main()
