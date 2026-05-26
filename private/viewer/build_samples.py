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
# Primary source: national/corpus/ hive-partitioned parquet (20 outlets,
# clean schema [url, pub_date, title, full_text, word_count, source, year_month]).
# Additional CSVs (rbc_fulltext, izvestia_fulltext) covered as fallback.
RM_NATIONAL = RM_PROC / "national" / "corpus"
RM_EXTRA_CSVS = [
    (RM_PROC / "rbc_national" / "rbc_fulltext.csv",   "rbc_national"),
    (RM_PROC / "izvestia"     / "izvestia_fulltext.csv", "izvestia"),
]


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


def build_rusmedia():
    import pyarrow.parquet as pq
    import csv as csvmod
    csvmod.field_size_limit(sys.maxsize)
    out = []

    # --- 1) national/corpus hive-partitioned parquets ---
    if RM_NATIONAL.exists():
        sources = sorted(p for p in RM_NATIONAL.glob("source=*") if p.is_dir())
        print(f"rusmedia: {len(sources)} sources in national/corpus")
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

    # --- 2) extra CSVs (rbc + izvestia fulltext, not in national/) ---
    # RAM-safe: reservoir-sample K rows in one streaming pass — never load
    # the whole CSV into memory. Memory bounded at O(K) row-dicts regardless
    # of file size (the rbc fulltext CSV is 600 MB, izvestia 452 MB).
    TARGET = 120
    for csv_path, sname in RM_EXTRA_CSVS:
        if not csv_path.exists(): continue
        try:
            reservoir = []
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                rdr = csvmod.DictReader(f)
                for i, row in enumerate(rdr):
                    if i < TARGET:
                        reservoir.append(row)
                    else:
                        j = random.randint(0, i)
                        if j < TARGET:
                            reservoir[j] = row
            for r in reservoir:
                item = normalize_rusmedia_row(r, sname)
                if item: out.append(item)
        except Exception as e:
            print(f"  WARN {csv_path.name}: {e}", file=sys.stderr)

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
