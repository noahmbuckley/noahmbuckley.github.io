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
# rusMedia is heterogeneous CSVs. We accept any file with a text-bearing column
# from this list (in priority order). Files without text-bearing columns are skipped.
TEXT_FIELDS  = ("full_text", "text", "description")
TITLE_FIELDS = ("title",)
URL_FIELDS   = ("url",)
DATE_FIELDS  = ("date", "pub_date", "pubDate", "published_time", "lastmod")
REGION_FIELDS = ("regionid",)
SOURCE_FIELDS = ("portal", "source", "city", "region", "category")


def first_present(row, keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, "", float("nan")): return v
    return None


def normalize_rusmedia(row, csv_path):
    txt = first_present(row, TEXT_FIELDS)
    if not txt: return None
    url = first_present(row, URL_FIELDS)
    src = first_present(row, SOURCE_FIELDS) or csv_path.stem.split("_")[0]
    return {
        "id": f"rm_{csv_path.stem}_{row.get('url_id') or row.get('article_id') or hash(str(url) or txt[:60])}",
        "db": "rusmedia",
        "date": first_present(row, DATE_FIELDS),
        "source": str(src),
        "title": first_present(row, TITLE_FIELDS),
        "text": truncate(txt),
        "url": url if url else None,
        "regionid": first_present(row, REGION_FIELDS),
        "metadata": {
            "csv_file": csv_path.name,
            "category": row.get("category"),
            "view_count": row.get("view_count"),
            "author": row.get("author"),
            "word_count": row.get("word_count"),
        },
    }


def build_rusmedia():
    import csv as csvmod
    csvmod.field_size_limit(sys.maxsize)
    paths = sorted(RM_PROC.glob("*.csv"))
    text_bearing = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                hdr = f.readline().rstrip("\n").split(",")
                if any(c in hdr for c in TEXT_FIELDS):
                    text_bearing.append(p)
        except Exception:
            pass
    print(f"rusmedia: {len(paths)} CSVs total, {len(text_bearing)} with text bodies")
    if not text_bearing: return []
    # weight selection by file row count so big files contribute more
    per_file = max(20, N_PER_DB // max(1, len(text_bearing)))
    out = []
    for p in text_bearing:
        if len(out) >= N_PER_DB * 2: break
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                rdr = csvmod.DictReader(f)
                rows = list(rdr)
            if not rows: continue
            pick = random.sample(rows, min(per_file, len(rows)))
            for r in pick:
                item = normalize_rusmedia(r, p)
                if item: out.append(item)
        except Exception as e:
            print(f"  WARN {p.name}: {e}", file=sys.stderr)
    random.shuffle(out)
    print(f"  -> {len(out[:N_PER_DB])} items (from {len(out)} candidates)")
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
