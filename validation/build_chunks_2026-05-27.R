##### build_chunks_2026-05-27.R #####
# Four new chunks for the iPad validator, building on the dedup library +
# protest-from-media pipeline we just shipped:
#
#   1. scope-filter-drops-A    — 60 items, audit the new scope_filter Layer 1
#      (https://...)                drops on the Activatica corpus
#   2. protests-fresh-C        — 100 Shkulev (rusMedia) protest-keyword candidates
#   3. protests-fresh-D        — 100 Telegram (rusSocial) protest-keyword candidates
#   4. protests-fresh-E        — 100 REGNUM protest-keyword candidates
#                                (pre-2012 backward-extension gold)
#
# Each writes data/<chunk_id>/{items.json, schema.json}. tasks.json is updated
# at the end (preserving the existing 5 fresh chunks).
#
# Strata principles (in order of priority):
#   - Cover the new sources we didn't sample before (C/D/E).
#   - Lean into known failure modes today (region.country=NA → Cyrillic
#     fallback; detention-without-protest false positives).
#   - Pre-2012 REGNUM for the chronological gap FPP can't reach.

rm(list = ls())
suppressMessages({ library(jsonlite) })
set.seed(20260527)

##### PATHS #####
val_root <- "/Users/noahbuckley/Dropbox/Projects/me/website/validation"
data_dir <- file.path(val_root, "data")
EV       <- "/Users/noahbuckley/Dropbox/Projects/eventsData/output"
TODAY    <- "2026-05-27"

##### HELPERS #####
take_n <- function(df, n) {
  if (is.null(df) || nrow(df) == 0) return(df[0, ])
  df[sample.int(nrow(df), min(n, nrow(df))), , drop = FALSE]
}

write_chunk <- function(chunk_id, items_df, schema_list) {
  d <- file.path(data_dir, chunk_id)
  dir.create(d, showWarnings = FALSE, recursive = TRUE)
  items_out <- list(task_id = chunk_id, schema_version = 1L,
                    built_at = TODAY, n_items = nrow(items_df),
                    items = items_df)
  writeLines(toJSON(items_out, auto_unbox = TRUE, na = "null", pretty = FALSE),
             file.path(d, "items.json"))
  schema_list$task_id <- chunk_id
  schema_list$version <- TODAY
  writeLines(toJSON(schema_list, auto_unbox = TRUE, na = "null", pretty = TRUE),
             file.path(d, "schema.json"))
  cat(sprintf("  wrote %s (%d items)\n", chunk_id, nrow(items_df)))
}

##### SHARED SCHEMA: protest verdict fields (re-used by C / D / E) #####
protest_verdict_fields <- list(
  list(field = "verdict",
       label = "Is this a real protest event?",
       type = "enum", required = TRUE,
       options = list(
         list(value = "YES",        label = "YES — real protest",    key = "1", tone = "good"),
         list(value = "NO",         label = "NO — not a protest",    key = "2", tone = "bad"),
         list(value = "BORDERLINE", label = "BORDERLINE",            key = "3", tone = "warn"),
         list(value = "SKIP",       label = "SKIP — can't tell",     key = "4", tone = "neutral"))),
  list(field = "protest_type",
       label = "Protest type",
       type = "enum",
       options = list(
         list(value = "political",     label = "political"),
         list(value = "local_issue",   label = "local_issue"),
         list(value = "labor",         label = "labor"),
         list(value = "environmental", label = "environmental"),
         list(value = "civic",         label = "civic"),
         list(value = "other",         label = "other")),
       show_if = list(verdict = c("YES", "BORDERLINE"))),
  list(field = "scope",
       label = "Scope",
       type = "enum",
       options = list(
         list(value = "national", label = "national"),
         list(value = "regional", label = "regional"),
         list(value = "local",    label = "local")),
       show_if = list(verdict = c("YES", "BORDERLINE"))),
  list(field = "repression",
       label = "Repression",
       type = "enum",
       options = list(
         list(value = "none",       label = "none"),
         list(value = "detentions", label = "detentions"),
         list(value = "dispersal",  label = "dispersal"),
         list(value = "violence",   label = "violence")),
       show_if = list(verdict = c("YES", "BORDERLINE"))),
  list(field = "regionid_correct",
       label = "regionid_publisher matches the event?",
       type = "enum",
       options = list(
         list(value = "yes",       label = "Yes"),
         list(value = "no",        label = "No (federal / wrong region)"),
         list(value = "cant_tell", label = "Can't tell")),
       show_if = list(verdict = c("YES", "BORDERLINE")))
)

protest_display <- list(
  list(field = "date",                label = "Date"),
  list(field = "region_label",        label = "regionid_publisher", format = "compact"),
  list(field = "channel_or_portal",   label = "Source",             format = "compact"),
  list(field = "title",               label = "Title (RU)",         format = "longtext"),
  list(field = "text",                label = "Text (RU)",          format = "longtext"),
  list(field = "kw_core",             label = "Core kw",            format = "tag"),
  list(field = "kw_detention",        label = "Detention kw",       format = "tag"),
  list(field = "url",                 label = "URL",                format = "link"),
  list(field = "strata",              label = "Strata",             format = "tag")
)

# regionid label lookup (reused from build_chunks_2026-05-26.R region_lookup)
RL <- list()
for (d in list.files(data_dir, pattern = "^arrests-", full.names = TRUE)) {
  f <- file.path(d, "items.json")
  if (!file.exists(f)) next
  j <- tryCatch(fromJSON(f, simplifyVector = TRUE), error = function(e) NULL)
  items <- if (is.list(j) && "items" %in% names(j)) j$items else j
  if (!is.data.frame(items) || !"region_event" %in% names(items)) next
  for (i in seq_len(nrow(items))) {
    key <- sub(" .*", "", items$region_event[i])
    RL[[as.character(key)]] <- items$region_event[i]
  }
}
fmt_region <- function(rid) {
  if (is.na(rid) || rid == "") return(NA_character_)
  v <- RL[[as.character(rid)]]
  if (is.null(v) || is.na(v)) sprintf("%s · ?", rid) else as.character(v)
}

##### CHUNK 1: scope-filter-drops-A #####
cat("\n===== chunk 1: scope-filter-drops-A =====\n")
drops <- read.csv(file.path(EV, "scope_filter_drops_activatica_2026-05-27.csv"),
                  stringsAsFactors = FALSE, encoding = "UTF-8")
cat("total drops:", nrow(drops), "| by reason:\n")
print(table(drops$drop_reason))

# Stratify within country:non_russia by country (top 5), then a small grab-bag.
non_ru <- drops[drops$drop_reason == "country:non_russia", ]
top_cty <- names(sort(table(non_ru$region_country), decreasing = TRUE))[1:5]
cat("\ntop 5 dropped countries:", paste(top_cty, collapse = " · "), "\n")
non_ru_strat <- do.call(rbind, lapply(top_cty,
  function(c) {
    sub <- non_ru[non_ru$region_country == c, ]
    s <- take_n(sub, 10); s$strata <- paste0("country:", c); s
  }))
other_reasons <- drops[drops$drop_reason != "country:non_russia", ]
other_reasons$strata <- other_reasons$drop_reason
chunk1 <- rbind(non_ru_strat, other_reasons)
chunk1$item_id <- chunk1$item_id    # already named correctly
chunk1 <- chunk1[, c("item_id", "drop_reason", "strata", "region_country",
                     "region_name", "title", "text_excerpt", "start",
                     "createdAt", "url")]
cat("scope-filter-drops-A:", nrow(chunk1), "items\n")

drops_schema <- list(
  task_id = "scope-filter-drops-A",
  name    = "scope-filter drops — audit (60 items)",
  version = TODAY,
  id_field = "item_id",
  instructions = paste0(
    "60 items the new scope_filter (eventsData/dedup/) dropped from the Activatica corpus on ",
    TODAY, ". Verify each drop is correct — we want to catch any silent data loss. ",
    "Stratified across top-5 dropped countries + the small region:* / quality:* buckets. ",
    "Run quarterly or after any scope_filter change."),
  display = list(
    list(field = "drop_reason",     label = "Drop reason",         format = "tag"),
    list(field = "strata",          label = "Stratum",             format = "tag"),
    list(field = "region_country",  label = "region.country",      format = "compact"),
    list(field = "region_name",     label = "region.name",         format = "compact"),
    list(field = "title",           label = "Title",               format = "longtext"),
    list(field = "text_excerpt",    label = "Text excerpt",        format = "longtext"),
    list(field = "start",           label = "Event date"),
    list(field = "url",             label = "URL",                 format = "link")
  ),
  validation = list(
    list(field = "verdict",
         label = "Was this drop correct?",
         type = "enum", required = TRUE,
         options = list(
           list(value = "drop_correct", label = "Drop is CORRECT (truly out-of-scope)",
                key = "1", tone = "good"),
           list(value = "should_keep",  label = "Drop is WRONG (Russia-relevant; keep)",
                key = "2", tone = "bad"),
           list(value = "unclear",      label = "Unclear / borderline",
                key = "3", tone = "warn")))
  )
)
write_chunk("scope-filter-drops-A", chunk1, drops_schema)

##### CHUNKS 2-4: protest candidates from each source #####

prep_protest_chunk <- function(df, strata_col_built_already = NULL) {
  # Common transforms: build region_label, ensure column set matches schema display.
  if (is.null(df) || nrow(df) == 0) return(df[0, ])
  df$region_label <- vapply(df$regionid_publisher, fmt_region, character(1))
  df$item_id <- as.character(df$id)
  if (!is.null(strata_col_built_already) && strata_col_built_already %in% names(df)) {
    df$strata <- df[[strata_col_built_already]]
  }
  cols <- c("item_id", "date", "region_label", "channel_or_portal",
            "title", "text", "kw_core", "kw_detention", "url", "strata")
  for (c in cols) if (!c %in% names(df)) df[[c]] <- ""
  df[, cols]
}

make_protest_schema <- function(task_id, name, instructions) {
  list(task_id = task_id, name = name, version = TODAY,
       id_field = "item_id", instructions = instructions,
       display = protest_display, validation = protest_verdict_fields)
}

##### CHUNK 2: protests-fresh-C — Shkulev #####
cat("\n===== chunk 2: protests-fresh-C (Shkulev) =====\n")
shk <- read.csv(file.path(EV, "rusmedia_protest_articles.csv"),
                stringsAsFactors = FALSE, encoding = "UTF-8")
shk$year <- as.integer(shk$year)
shk$has_detention <- nchar(shk$kw_detention) > 0
cat("Shkulev pool:", nrow(shk), "| with detention:", sum(shk$has_detention), "\n")

# Strata: 30 by year band, 30 by region category, 25 with detention, 15 borderline (single kw_core hit).
get_band <- function(y) ifelse(is.na(y), NA, ifelse(y <= 2014, "2010-2014",
                        ifelse(y <= 2019, "2015-2019", "2020-2025")))
shk$band <- get_band(shk$year)
shk_year <- do.call(rbind, lapply(c("2010-2014","2015-2019","2020-2025"),
  function(b) {
    sub <- shk[!is.na(shk$band) & shk$band == b, ]
    s <- take_n(sub, 10); s$strata <- paste0("year:", b); s
  }))
# Region buckets — by candidate count
reg_counts <- sort(table(shk$regionid_publisher), decreasing = TRUE)
big5     <- names(reg_counts)[1:5]
mid_slice <- names(reg_counts)[6:15]
small    <- names(reg_counts)[16:length(reg_counts)]
shk_big <- take_n(shk[shk$regionid_publisher %in% big5 & !shk$id %in% shk_year$id, ], 10)
shk_mid <- take_n(shk[shk$regionid_publisher %in% mid_slice & !shk$id %in% shk_year$id, ], 10)
shk_sml <- take_n(shk[shk$regionid_publisher %in% small & !shk$id %in% shk_year$id, ], 10)
shk_big$strata <- "region:big5"; shk_mid$strata <- "region:mid"; shk_sml$strata <- "region:small"
shk_det <- take_n(shk[shk$has_detention &
                        !shk$id %in% c(shk_year$id, shk_big$id, shk_mid$id, shk_sml$id), ], 25)
shk_det$strata <- "with_detention"
shk_borderline <- shk[!grepl(";", shk$kw_core) &
                       !shk$id %in% c(shk_year$id, shk_big$id, shk_mid$id, shk_sml$id, shk_det$id), ]
shk_borderline <- take_n(shk_borderline, 15)
shk_borderline$strata <- "borderline_kw"
chunk_C <- rbind(shk_year, shk_big, shk_mid, shk_sml, shk_det, shk_borderline)
chunk_C <- prep_protest_chunk(chunk_C, "strata")
chunk_C <- chunk_C[sample.int(nrow(chunk_C)), ]
write_chunk("protests-fresh-C", chunk_C,
            make_protest_schema(
              "protests-fresh-C",
              sprintf("Protests — Shkulev media (%d items)", nrow(chunk_C)),
              paste0("Protest candidates from rusMedia Shkulev portal titles ",
                     "(see eventsData/code/17_rusmedia_protest_search.py). ",
                     "Stratified by year band, region size, detention-keyword, and ",
                     "borderline single-keyword matches. Verify each is a real protest ",
                     "event; flag where regionid_publisher doesn't match the event region.")))

##### CHUNK 3: protests-fresh-D — Telegram #####
cat("\n===== chunk 3: protests-fresh-D (Telegram) =====\n")
tg <- read.csv(file.path(EV, "telegram_protest_posts.csv"),
               stringsAsFactors = FALSE, encoding = "UTF-8")
tg$views <- suppressWarnings(as.integer(tg$views)); tg$views[is.na(tg$views)] <- 0
tg$year  <- as.integer(tg$year)
tg$has_detention <- nchar(tg$kw_detention) > 0
cat("Telegram pool:", nrow(tg), "| with detention:", sum(tg$has_detention), "\n")

# Strata: 50 by channel_type (10 each from news/incidents/official/governor_personal/local),
# 25 high-views (top 5%), 15 with detention, 10 by year (2 each from 2020-2024).
ctype_strat <- do.call(rbind, lapply(
  c("news","incidents","official","governor_personal","local"),
  function(ct) {
    sub <- tg[tg$channel_type == ct, ]
    s <- take_n(sub, 10); s$strata <- paste0("ctype:", ct); s
  }))
views_cut <- quantile(tg$views[tg$views > 0], 0.95, na.rm = TRUE)
tg_high <- tg[tg$views >= views_cut & !tg$id %in% ctype_strat$id, ]
tg_high <- take_n(tg_high, 25); tg_high$strata <- "high_views"
tg_det <- take_n(tg[tg$has_detention &
                      !tg$id %in% c(ctype_strat$id, tg_high$id), ], 15)
tg_det$strata <- "with_detention"
tg_year <- do.call(rbind, lapply(2020:2024, function(y) {
  sub <- tg[tg$year == y & !tg$id %in% c(ctype_strat$id, tg_high$id, tg_det$id), ]
  s <- take_n(sub, 2); s$strata <- paste0("year:", y); s
}))
chunk_D <- rbind(ctype_strat, tg_high, tg_det, tg_year)
chunk_D <- prep_protest_chunk(chunk_D, "strata")
chunk_D <- chunk_D[sample.int(nrow(chunk_D)), ]
write_chunk("protests-fresh-D", chunk_D,
            make_protest_schema(
              "protests-fresh-D",
              sprintf("Protests — Telegram (%d items)", nrow(chunk_D)),
              paste0("Protest candidates from rusSocial Telegram posts (see ",
                     "eventsData/code/18_telegram_protest_search.py, 705K candidates). ",
                     "Stratified by channel_type, view-count, detention-keyword, and ",
                     "year. The detention-keyword stratum specifically tests the ",
                     "proxy: a detention mention is often a protest signal, sometimes ",
                     "ordinary crime — verdict tells us how often.")))

##### CHUNK 4: protests-fresh-E — REGNUM #####
cat("\n===== chunk 4: protests-fresh-E (REGNUM) =====\n")
rg <- read.csv(file.path(EV, "regnum_protest_articles.csv"),
               stringsAsFactors = FALSE, encoding = "UTF-8")
rg$year <- as.integer(rg$year)
rg$in_title <- as.logical(rg$in_title)
cat("REGNUM pool:", nrow(rg), "| pre-2012:", sum(rg$year < 2012, na.rm = TRUE),
    "| in_body_only:", sum(!rg$in_title, na.rm = TRUE), "\n")

# Strata: 50 pre-2012 (backward extension gold), 30 2012-2020, 20 in-body-only
rg_pre  <- rg[!is.na(rg$year) & rg$year < 2012, ]
rg_pre  <- take_n(rg_pre, 50); rg_pre$strata  <- "pre_2012"
rg_mid  <- rg[!is.na(rg$year) & rg$year >= 2012 & rg$year <= 2020 &
              !rg$id %in% rg_pre$id, ]
rg_mid  <- take_n(rg_mid, 30); rg_mid$strata  <- "2012-2020"
rg_body <- rg[!rg$in_title & !rg$id %in% c(rg_pre$id, rg_mid$id), ]
rg_body <- take_n(rg_body, 20); rg_body$strata <- "in_body_only"
chunk_E <- rbind(rg_pre, rg_mid, rg_body)
chunk_E <- prep_protest_chunk(chunk_E, "strata")
chunk_E <- chunk_E[sample.int(nrow(chunk_E)), ]
write_chunk("protests-fresh-E", chunk_E,
            make_protest_schema(
              "protests-fresh-E",
              sprintf("Protests — REGNUM (%d items)", nrow(chunk_E)),
              paste0("Protest candidates from REGNUM articles (see ",
                     "eventsData/code/19_regnum_protest_search.py, 9.3K candidates). ",
                     "Heavy on pre-2012 for the backward-extension gold that FPP ",
                     "can't reach. in_body_only stratum tests whether body-matched ",
                     "candidates (title doesn't trigger) are usable.")))

##### UPDATE tasks.json — preserve the existing 5 entries, append the 4 new #####
tj <- fromJSON(file.path(val_root, "tasks.json"), simplifyVector = FALSE)
existing_ids <- vapply(tj$tasks, function(t) t$id, character(1))
new_tasks <- list(
  list(id = "scope-filter-drops-A",
       name = "scope-filter drops — audit (60)",
       project = "dedup",
       description = paste0("60 items the new scope_filter dropped from the ",
                            "Activatica corpus (", TODAY, "). Verify each drop ",
                            "is correct — silent-data-loss audit."),
       schema_url = "data/scope-filter-drops-A/schema.json",
       items_url  = "data/scope-filter-drops-A/items.json"),
  list(id = "protests-fresh-C",
       name = "Protests — Shkulev media (100)",
       project = "protests",
       description = paste0("100 protest candidates from Shkulev portal titles, ",
                            "stratified by year/region/detention/borderline. Built ",
                            TODAY, "."),
       schema_url = "data/protests-fresh-C/schema.json",
       items_url  = "data/protests-fresh-C/items.json"),
  list(id = "protests-fresh-D",
       name = "Protests — Telegram (100)",
       project = "protests",
       description = paste0("100 protest candidates from Telegram posts, ",
                            "stratified by channel_type/views/detention/year. Built ",
                            TODAY, "."),
       schema_url = "data/protests-fresh-D/schema.json",
       items_url  = "data/protests-fresh-D/items.json"),
  list(id = "protests-fresh-E",
       name = "Protests — REGNUM (100)",
       project = "protests",
       description = paste0("100 protest candidates from REGNUM (heavy pre-2012). ",
                            "Built ", TODAY, "."),
       schema_url = "data/protests-fresh-E/schema.json",
       items_url  = "data/protests-fresh-E/items.json")
)
# de-dup by id (rebuilds preserve insertion order)
keep_existing <- Filter(function(t) !t$id %in% sapply(new_tasks, function(n) n$id), tj$tasks)
tj$tasks <- c(keep_existing, new_tasks)
tj$generated_at <- TODAY
writeLines(toJSON(tj, auto_unbox = TRUE, na = "null", pretty = TRUE),
           file.path(val_root, "tasks.json"))
cat(sprintf("\nupdated tasks.json — now %d tasks total\n", length(tj$tasks)))

cat("\nDONE.  next: render + push the validator site so the iPad picks them up.\n")
