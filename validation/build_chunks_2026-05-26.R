##### build_chunks_2026-05-26.R #####
# Reboot the iPad validation queue: 5 fresh chunks of 100 items each (was 4 of
# 200), targeted at the highest-value gaps:
#   1. arrests-fresh-A  — 50 carry-forward + 50 new media-corpus (regional officials)
#   2. arrests-fresh-B  — 50 carry-forward + 50 federal/sledcom/multi-defendant edges
#   3. protests-fresh-A — 100 from activatica pilot, stratified by classifier output
#   4. protests-fresh-B — 100 FPP-text protests stratified by llm_protest_type (TYPE gold)
#   5. disaster-types   — 100 stratified by disaster_type, asking for type + severity gold
#
# Writes data/<chunk>/items.json + schema.json. Old chunks stay on disk (the loader
# still sees them); only tasks.json is replaced so the iPad shows only the new five.

rm(list = ls())
suppressMessages({ library(jsonlite); library(readxl) })
set.seed(20260526)

##### PATHS #####
val_root <- "/Users/noahbuckley/Dropbox/Projects/me/website/validation"
data_dir <- file.path(val_root, "data")
EV       <- "/Users/noahbuckley/Dropbox/Projects/eventsData/output"
DIS      <- "/Users/noahbuckley/Dropbox/Projects/disaster/data/processed"
EXPORTS  <- "~/Dropbox/_validation_exports"
TODAY    <- "2026-05-26"

##### HELPERS #####
load_first_df <- function(p) {
  e <- new.env(); load(p, envir = e)
  dfs <- Filter(function(o) is.data.frame(get(o, e)), ls(e))
  get(dfs[[which.max(sapply(dfs, function(o) nrow(get(o, e))))]], e)
}
write_chunk <- function(chunk_id, items_df, schema_list) {
  d <- file.path(data_dir, chunk_id); dir.create(d, showWarnings = FALSE, recursive = TRUE)
  items_out <- list(task_id = chunk_id, schema_version = 1L,
                    built_at = TODAY, n_items = nrow(items_df),
                    items = items_df)
  writeLines(toJSON(items_out, auto_unbox = TRUE, na = "null", pretty = FALSE),
             file.path(d, "items.json"))
  schema_list$task_id <- chunk_id; schema_list$version <- TODAY
  writeLines(toJSON(schema_list, auto_unbox = TRUE, na = "null", pretty = TRUE),
             file.path(d, "schema.json"))
  cat(sprintf("wrote %s (%d items)\n", chunk_id, nrow(items_df)))
}

##### regionid -> "regionid · name" using existing items.json lookup #####
build_region_lookup <- function() {
  lk <- list()
  for (d in list.files(data_dir, pattern = "^arrests-sample-|^disaster-sample-", full.names = TRUE)) {
    f <- file.path(d, "items.json"); if (!file.exists(f)) next
    j <- tryCatch(fromJSON(f, simplifyVector = TRUE), error = function(e) NULL)
    items <- if (is.list(j) && "items" %in% names(j)) j$items else j
    if (is.null(items)) next
    if (!is.data.frame(items)) items <- as.data.frame(items)
    # region_event in arrests is "rid · Name"; in disaster: regionid + region columns
    if ("region_event" %in% names(items) && "regionid" %in% names(items)) {
      for (i in seq_len(nrow(items))) lk[[as.character(items$regionid[i])]] <- items$region_event[i]
    } else if ("region" %in% names(items) && "regionid" %in% names(items)) {
      for (i in seq_len(nrow(items)))
        lk[[as.character(items$regionid[i])]] <- sprintf("%s · %s", items$regionid[i], substr(items$region[i],1,18))
    }
  }
  lk
}
RL <- build_region_lookup()
fmt_region <- function(rid) {
  if (is.na(rid)) return(NA_character_)
  v <- RL[[as.character(rid)]]
  if (is.null(v) || is.na(v)) sprintf("%s · ?", rid) else as.character(v)
}

##### LOAD CARRY-FORWARD: arrests sample-A unanswered #####
cat("\n===== carry-forward inventory =====\n")
sa_items_raw <- fromJSON(file.path(data_dir, "arrests-sample-A/items.json"), simplifyVector = TRUE)
sa_items <- if (is.list(sa_items_raw) && "items" %in% names(sa_items_raw)) sa_items_raw$items else sa_items_raw
sa_export <- fromJSON(file.path(EXPORTS, "validation_arrests-sample-A_2026-05-17.json"),
                      simplifyVector = FALSE)
answered_ids <- vapply(sa_export$items, function(x)
  if (!is.null(x$answer) && !is.null(x$answer$verdict)) as.character(x$item_id) else NA_character_,
  character(1))
answered_ids <- answered_ids[!is.na(answered_ids)]
sa_unans <- sa_items[!sa_items$item_id %in% answered_ids, ]
cat("arrests sample-A unanswered:", nrow(sa_unans), "by strata:\n")
print(sort(table(sa_unans$strata), decreasing = TRUE))

##### CHUNK 1: arrests-fresh-A — region mismatch + media regional officials #####
# 50 carry-forward (highest-value strata) + 50 new media items
priority1_strata <- c("Region mismatch (publisher ≠ event)",
                      "Multi-defendant (name has ; or 2+ names)",
                      "regionid_confidence = low",
                      "Telegram (LLM-region-extracted)",
                      "Shkulev (LLM-region-extracted)")
cf1 <- sa_unans[sa_unans$strata %in% priority1_strata, ]
cf1 <- cf1[order(match(cf1$strata, priority1_strata)), ]
cf1 <- cf1[seq_len(min(50, nrow(cf1))), ]
cat("\nchunk 1 carry-forward (priority strata):", nrow(cf1), "\n")
print(table(cf1$strata))

# 50 NEW media-source items not yet sampled
am <- load_first_df(file.path(EV, "arrests_master.Rdata"))
already <- unique(c(sa_items$item_id))   # don't re-sample anything already in iPad
am$date <- sprintf("%04d-%02d-%02d", am$year, am$month, ifelse(is.na(am$day), 0L, am$day))
am$regionid <- as.integer(am$regionid)
new_media <- am[am$source %in% c("shkulev", "telegram") &
                !is.na(am$official_name) & nchar(am$official_name) > 2 &
                am$official_level %in% c("regional_minister","mayor","raion_head",
                                          "municipal_official","head_of_department",
                                          "head_of_enterprise") &
                !am$item_id %in% already &
                !is.na(am$text) & nchar(am$text) > 60, ]
cat("new media-source candidate pool:", nrow(new_media), "\n")
set.seed(101)
take_n <- function(df, n) df[sample.int(nrow(df), min(n, nrow(df))), , drop = FALSE]
new1 <- rbind(take_n(new_media[new_media$source == "shkulev", ], 25),
              take_n(new_media[new_media$source == "telegram", ], 25))

# Standardize to schema fields
to_arrests_item <- function(df, strata_label = NA) {
  data.frame(
    item_id = as.character(df$item_id), source = as.character(df$source),
    date = as.character(df$date),
    region_event = vapply(df$regionid, fmt_region, character(1)),
    region_publisher = vapply(df$regionid, fmt_region, character(1)),  # NEW items: no separate publisher
    region_mismatch_flag = FALSE,
    text = as.character(df$text),
    official_name = as.character(df$official_name),
    official_position = as.character(df$official_position),
    official_level = as.character(df$official_level),
    crime_type = as.character(df$crime_type),
    arrest_stage = as.character(df$arrest_stage),
    is_corruption = as.character(df$is_corruption),
    is_federal = as.character(df$official_level == "federal_in_region"),
    regionid_confidence = "high",
    strata = if (!is.na(strata_label)) strata_label else
             sprintf("%s (LLM-region-extracted)", tools::toTitleCase(as.character(df$source))),
    stringsAsFactors = FALSE)
}
new1_items <- to_arrests_item(new1)
# Carry-forward items already match the schema; ensure column alignment
cf1_aligned <- cf1[, names(new1_items)]
chunk1 <- rbind(cf1_aligned, new1_items)
chunk1 <- chunk1[sample.int(nrow(chunk1)), ]   # shuffle so carry/new interleave

##### CHUNK 2: arrests-fresh-B — federal / sledcom / multi-defendant / rare crime #####
priority2_strata <- c("is_federal = TRUE",
                      "Sledcom (publisher-region only)",
                      "Rare crime_type (violence/extremism/etc.)",
                      "Empty official_name but is_corruption=TRUE",
                      "Very short text (<50 chars)",
                      "FPP control (publisher-region only)")
cf2 <- sa_unans[sa_unans$strata %in% priority2_strata & !sa_unans$item_id %in% cf1$item_id, ]
cf2 <- cf2[order(match(cf2$strata, priority2_strata)), ]
cf2 <- cf2[seq_len(min(50, nrow(cf2))), ]
cat("\nchunk 2 carry-forward (level/source strata):", nrow(cf2), "\n")
print(table(cf2$strata))

new_fed <- am[am$official_level == "federal_in_region" &
              !is.na(am$text) & nchar(am$text) > 50 &
              !am$item_id %in% c(already, chunk1$item_id), ]
new_sled <- am[am$source == "sledcom" & !is.na(am$official_name) &
               !am$item_id %in% c(already, chunk1$item_id), ]
rare_crimes <- c("violent_crime", "extremism", "treason", "espionage", "drugs", "tax_evasion")
new_rare <- am[!is.na(am$crime_type) & am$crime_type %in% rare_crimes &
               am$source %in% c("shkulev","telegram","sledcom") &
               !am$item_id %in% c(already, chunk1$item_id), ]
new_multi <- am[!is.na(am$official_name) &
                (grepl(";", am$official_name, fixed = TRUE) |
                 grepl(",", am$official_name, fixed = TRUE)) &
                am$source %in% c("shkulev","telegram","sledcom") &
                !am$item_id %in% c(already, chunk1$item_id), ]
new2 <- rbind(take_n(new_fed, 15), take_n(new_sled, 15),
              take_n(new_rare, 10), take_n(new_multi, 10))
new2_items <- to_arrests_item(new2)
new2_items$strata[1:nrow(new2_items)] <- c(
  rep("Federal in region (new)", min(15, nrow(new_fed))),
  rep("Sledcom (new)", min(15, nrow(new_sled))),
  rep("Rare crime_type (new)", min(10, nrow(new_rare))),
  rep("Multi-defendant (new)", min(10, nrow(new_multi))))[seq_len(nrow(new2_items))]
chunk2 <- rbind(cf2[, names(new2_items)], new2_items)
chunk2 <- chunk2[sample.int(nrow(chunk2)), ]

##### ARRESTS SCHEMA (reuse sample-A schema verbatim) #####
arrests_schema <- fromJSON(file.path(data_dir, "arrests-sample-A/schema.json"),
                           simplifyVector = FALSE)
arrests_schema$name <- "Arrests — verify (100 items)"
arrests_schema$instructions <- paste0(
  "100-item refresh (2026-05-26). Focused on the HIGH-VALUE strata you didn't get to ",
  "and fresh media-corpus picks. Pink-tinted rows are region-mismatch carry-forwards. ",
  "Yellow = LLM's call. Multi-defendant collapse + federal-vs-regional ambiguity ",
  "are the two recurring bugs to keep watching for.")

write_chunk("arrests-fresh-A", chunk1, arrests_schema)
arrests_schema$name <- "Arrests — verify (100 items, edges)"
write_chunk("arrests-fresh-B", chunk2, arrests_schema)

##### CHUNKS 3+4: PROTESTS #####
cat("\n===== protests =====\n")
act_raw <- fromJSON(file.path(data_dir, "protests-pilot-activatica/items.json"),
                    simplifyVector = TRUE)
act <- if (is.list(act_raw) && "items" %in% names(act_raw)) act_raw$items else act_raw
cat("activatica pool:", nrow(act), "| haiku_protest split:\n"); print(table(act$haiku_protest))
# CHUNK 3: 100 from activatica, stratified by haiku_protest x haiku_type
yes_pool <- act[act$haiku_protest == TRUE | act$haiku_protest == "TRUE", ]
no_pool  <- act[act$haiku_protest == FALSE | act$haiku_protest == "FALSE", ]
# 70 YES (stratified by haiku_type) + 30 NO
get_type_strat <- function(pool, total) {
  types <- na.omit(unique(pool$haiku_type)); types <- types[nzchar(types)]
  per <- max(1, floor(total / max(1, length(types))))
  out <- do.call(rbind, lapply(types, function(t) take_n(pool[pool$haiku_type == t, ], per)))
  if (nrow(out) > total) out <- out[seq_len(total), ]
  if (nrow(out) < total) {
    extra <- pool[!pool$id %in% out$id, ]
    out <- rbind(out, take_n(extra, total - nrow(out)))
  }
  out
}
chunk3_yes <- get_type_strat(yes_pool, 70)
chunk3_no  <- take_n(no_pool, 30)
chunk3 <- rbind(chunk3_yes, chunk3_no)
chunk3$item_id <- chunk3$id   # rename to match schema id_field convention
chunk3$strata  <- ifelse(chunk3$haiku_protest %in% c(TRUE, "TRUE"),
                         paste0("YES / ", chunk3$haiku_type), "NO (classifier)")
chunk3 <- chunk3[sample.int(nrow(chunk3)), ]

protests_schema <- fromJSON(file.path(data_dir, "protests-pilot-activatica/schema.json"),
                            simplifyVector = FALSE)
protests_schema$name <- "Protests — Activatica re-pick (100 items)"
protests_schema$id_field <- "item_id"
protests_schema$instructions <- paste0(
  "100-item refresh from the Activatica pilot (you hadn't answered any). ",
  "Stratified to give the classifier eval and the type/scope labels real signal. ",
  "Yellow = Haiku's call. We need TYPE labels especially — protest_type currently has 0 gold.")
write_chunk("protests-fresh-A", chunk3, protests_schema)

# CHUNK 4: FPP-text protests stratified by llm_protest_type (gives type gold for the FPP pop)
po <- load_first_df(file.path(EV, "protests_master.Rdata"))
fpp_pop <- po[!is.na(po$source_fpp) & po$source_fpp == TRUE &
              !is.na(po$fpp_eventdesc) & nchar(po$fpp_eventdesc) > 40 &
              !is.na(po$llm_protest_type), ]
cat("FPP-text protests with llm_protest_type:", nrow(fpp_pop), "\n")
print(sort(table(fpp_pop$llm_protest_type), decreasing = TRUE))
types4 <- names(sort(table(fpp_pop$llm_protest_type), decreasing = TRUE))
per_type <- max(8, ceiling(100 / length(types4)))
chunk4_rows <- do.call(rbind, lapply(types4, function(t) take_n(fpp_pop[fpp_pop$llm_protest_type == t, ], per_type)))
chunk4_rows <- chunk4_rows[seq_len(min(100, nrow(chunk4_rows))), ]
chunk4 <- data.frame(
  item_id = paste0("pfpp_", chunk4_rows$fpp_eventid, "_", chunk4_rows$regionid, "_",
                   format(as.Date(chunk4_rows$date), "%Y%m")),
  date = as.character(chunk4_rows$date),
  region_event = vapply(chunk4_rows$regionid, fmt_region, character(1)),
  regionid = as.integer(chunk4_rows$regionid),
  text = as.character(chunk4_rows$fpp_eventdesc),
  haiku_protest = TRUE,
  haiku_type = as.character(chunk4_rows$llm_protest_type),
  haiku_type_rus = as.character(chunk4_rows$llm_protest_type),
  haiku_scope = as.character(chunk4_rows$llm_national_campaign),
  haiku_regime_crit = as.character(chunk4_rows$llm_against_regime),
  haiku_size = as.character(chunk4_rows$llm_participants),
  strata = paste0("FPP / ", chunk4_rows$llm_protest_type),
  stringsAsFactors = FALSE)
chunk4 <- chunk4[sample.int(nrow(chunk4)), ]

protests_schema$name <- "Protests — FPP type labeling (100 items)"
protests_schema$instructions <- paste0(
  "100 FPP-source protest events, stratified by llm_protest_type. Goal: TYPE gold ",
  "for the FPP population (currently 0 gold). Confirm protest YES/NO and the type ",
  "label. Many will be straightforward; the unsure ones are the most valuable.")
write_chunk("protests-fresh-B", chunk4, protests_schema)

##### CHUNK 5: DISASTER — type + severity gold #####
cat("\n===== disaster types =====\n")
dm <- load_first_df(file.path(DIS, "disasters_master_v3.Rdata"))
# Use the broad-but-clean pool: Layer-2 verdict YES + has eventdesc + has disaster_type
dm$date <- sprintf("%04d-%02d-00", dm$year, dm$month)   # month-precision (no day in v3)
dpool <- dm[!is.na(dm$disaster_type) & nzchar(dm$disaster_type) &
            !is.na(dm$eventdesc) & nchar(dm$eventdesc) > 30, ]
# Layer-2 LLM filter column is llm_verdict; keep YES/BORDERLINE/missing
if ("llm_verdict" %in% names(dpool))
  dpool <- dpool[is.na(dpool$llm_verdict) | dpool$llm_verdict %in% c("YES","BORDERLINE"), ]
cat("disaster type-gold pool:", nrow(dpool), "\n")
# Exclude items already hand-verdicted
verdicted_ids <- character(0)
ah <- file.path(DIS, "verification/all_handcoded.csv")
if (file.exists(ah)) {
  hc <- read.csv(ah, stringsAsFactors = FALSE)
  verdicted_ids <- as.character(hc$eventid[!is.na(hc$verdict) & nzchar(hc$verdict)])
}
dpool <- dpool[!as.character(dpool$eventid) %in% verdicted_ids, ]
cat("after excluding already-verdicted:", nrow(dpool), "\n")
types5 <- names(sort(table(dpool$disaster_type), decreasing = TRUE))[1:10]
per5 <- 10
chunk5_rows <- do.call(rbind, lapply(types5, function(t) take_n(dpool[dpool$disaster_type == t, ], per5)))
chunk5_rows <- chunk5_rows[seq_len(min(100, nrow(chunk5_rows))), ]

sev_col <- if ("severity_recal" %in% names(chunk5_rows)) "severity_recal" else "severity"
chunk5 <- data.frame(
  item_id      = as.character(chunk5_rows$eventid),
  date         = as.character(chunk5_rows$date),
  region       = as.character(chunk5_rows$region),
  regionid     = as.integer(chunk5_rows$regionid),
  eventdesc    = as.character(chunk5_rows$eventdesc),
  disaster_type    = as.character(chunk5_rows$disaster_type),     # LLM call (yellow)
  severity         = as.character(chunk5_rows[[sev_col]]),         # LLM call (yellow)
  deaths           = if ("deaths" %in% names(chunk5_rows)) as.character(chunk5_rows$deaths) else NA_character_,
  primary_type     = if ("primary_type" %in% names(chunk5_rows)) as.character(chunk5_rows$primary_type) else "disaster_accident",
  strata           = paste0("type:", chunk5_rows$disaster_type),
  stringsAsFactors = FALSE)
chunk5 <- chunk5[sample.int(nrow(chunk5)), ]

# Disaster TYPE schema — fresh, focused on type + severity correction
disaster_types <- c("fire","disease_outbreak","infrastructure_failure","mass_poisoning",
                    "environmental_contamination","transport_accident","building_collapse",
                    "explosion","heating_failure","water_supply","industrial_accident",
                    "flood","gas_explosion","military_accident","wildfire","other_disaster")
mkopt <- function(v, lab = v, key = NULL, tone = "neutral") {
  o <- list(value = v, label = lab, tone = tone); if (!is.null(key)) o$key <- key; o
}
disaster_type_schema <- list(
  task_id = "disaster-types", name = "Disaster — type + severity gold (100 items)",
  version = TODAY, id_field = "item_id",
  instructions = paste0(
    "100 events confirmed to BE disasters (we're not re-asking yes/no). Goal: hand-",
    "correct the disaster TYPE and SEVERITY labels — both currently have 0 gold and ",
    "the model has nothing to score against. Yellow = LLM's current call. Just confirm ",
    "it's right, or pick the correct one. SEVERITY rubric: HIGH = ≥5 deaths or ",
    "mass evacuation or ≥3-day emergency regime; MEDIUM = 1-4 deaths or major ",
    "disruption; LOW = property damage only."),
  display = list(
    list(field = "strata", label = "Strata", format = "tag"),
    list(field = "date", label = "Date"),
    list(field = "region", label = "Region"),
    list(field = "regionid", label = "regionid", format = "compact"),
    list(field = "eventdesc", label = "Event (RU)", format = "longtext"),
    list(field = "disaster_type", label = "disaster_type", format = "compact", highlight = "llm"),
    list(field = "severity", label = "severity", format = "compact", highlight = "llm"),
    list(field = "deaths", label = "deaths (LLM)", format = "compact")
  ),
  validation = list(
    list(field = "type_correct", label = "Is disaster_type correct?",
         type = "enum", required = TRUE,
         options = list(mkopt("yes","Yes","1","good"),
                        mkopt("no","No — pick correct below","2","bad"),
                        mkopt("borderline","Borderline / overlap","3","warn"),
                        mkopt("not_a_disaster","Not a disaster (FP)","4","bad"))),
    list(field = "correct_type", label = "If 'no': correct type",
         type = "enum",
         options = lapply(disaster_types, function(t) mkopt(t, t)),
         show_if = list(type_correct = list("no","borderline"))),
    list(field = "correct_severity", label = "Correct severity",
         type = "enum", required = TRUE,
         options = list(mkopt("low","LOW","q","neutral"),
                        mkopt("medium","MEDIUM","w","warn"),
                        mkopt("high","HIGH","e","good"),
                        mkopt("cant_tell","Can't tell from text","r","neutral"))),
    list(field = "deaths_estimate", label = "Deaths (if mentioned)",
         type = "integer", placeholder = "0 if none"),
    list(field = "notes", label = "Notes / context", type = "textarea")
  )
)
write_chunk("disaster-types", chunk5, disaster_type_schema)

##### tasks.json — replace with ONLY the 5 new chunks #####
cat("\n===== tasks.json =====\n")
new_tasks <- list(
  schema_version = 1L, generated_at = TODAY,
  tasks = list(
    list(id = "arrests-fresh-A", name = "Arrests — region/multi-defendant (100)",
         project = "arrests",
         description = paste0("Fresh 100. 50 carry-forward from sample-A's hardest strata ",
                              "(region-mismatch, multi-defendant, low-conf, media-source). ",
                              "50 new media-corpus picks (Shkulev/Telegram regional officials). ",
                              "Built 2026-05-26."),
         schema_url = "data/arrests-fresh-A/schema.json",
         items_url  = "data/arrests-fresh-A/items.json"),
    list(id = "arrests-fresh-B", name = "Arrests — federal/sledcom/edges (100)",
         project = "arrests",
         description = paste0("Fresh 100. 50 carry-forward from sample-A (federal, sledcom, rare ",
                              "crime, empty-name+corruption). 50 new: federal-in-region, sledcom, ",
                              "rare crime_types, multi-defendant heuristics. Built 2026-05-26."),
         schema_url = "data/arrests-fresh-B/schema.json",
         items_url  = "data/arrests-fresh-B/items.json"),
    list(id = "protests-fresh-A", name = "Protests — Activatica re-pick (100)",
         project = "protests",
         description = paste0("100 from the unanswered Activatica pilot, stratified 70 YES (across ",
                              "haiku_type) + 30 NO. Unblocks the protest_type gold + the activatica ",
                              "audit-blocker. Built 2026-05-26."),
         schema_url = "data/protests-fresh-A/schema.json",
         items_url  = "data/protests-fresh-A/items.json"),
    list(id = "protests-fresh-B", name = "Protests — FPP type labeling (100)",
         project = "protests",
         description = paste0("100 FPP-text protests stratified across llm_protest_type. ",
                              "Goal: TYPE gold for the FPP population (currently 0 gold). ",
                              "Built 2026-05-26."),
         schema_url = "data/protests-fresh-B/schema.json",
         items_url  = "data/protests-fresh-B/items.json"),
    list(id = "disaster-types", name = "Disaster — type + severity gold (100)",
         project = "disaster",
         description = paste0("100 confirmed-disaster events stratified across disaster_type. ",
                              "Asks for hand-corrected TYPE + SEVERITY (both have 0 gold today). ",
                              "Excludes events already verdicted in all_handcoded.csv. ",
                              "Built 2026-05-26."),
         schema_url = "data/disaster-types/schema.json",
         items_url  = "data/disaster-types/items.json")
  ))
writeLines(toJSON(new_tasks, auto_unbox = TRUE, pretty = TRUE),
           file.path(val_root, "tasks.json"))
cat("wrote", file.path(val_root, "tasks.json"), "with", length(new_tasks$tasks), "tasks\n")

cat("\n===== DONE =====\n")
