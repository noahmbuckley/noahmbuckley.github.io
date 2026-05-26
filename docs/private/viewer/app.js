/* db viewer — load JSON sample, filter, render one item at a time.
   - DB tabs swap which JSON is "active"
   - filters (source, keyword, date range) build a derived index of matching ids
   - random / prev / next walk the filtered index
   - card renders title (if any) + source/date/url + full text + metadata table */

const DBS = ["telegram", "vk", "rusmedia"];
const cache = {};                   // db -> {items, sources, built_at, n_items}
const state = { db: "telegram", view: [], pos: 0 };

const $ = (id) => document.getElementById(id);

async function loadDB(db) {
  if (cache[db]) return cache[db];
  $("card").innerHTML = `<p class="placeholder">Loading ${db}…</p>`;
  const r = await fetch(`data/${db}.json`, { cache: "default" });
  if (!r.ok) throw new Error(`failed to load ${db}: HTTP ${r.status}`);
  const d = await r.json();
  cache[db] = d;
  return d;
}

function rebuildSourceDropdown() {
  const sel = $("source-filter");
  sel.innerHTML = '<option value="">— any —</option>';
  for (const s of cache[state.db].sources) {
    const o = document.createElement("option"); o.value = s; o.textContent = s;
    sel.appendChild(o);
  }
}

function applyFilters() {
  const all = cache[state.db].items;
  const src = $("source-filter").value;
  const kw  = $("keyword-filter").value.trim().toLowerCase();
  const from = $("date-from").value;        // YYYY-MM-DD
  const to   = $("date-to").value;
  state.view = all.filter(it => {
    if (src && it.source !== src) return false;
    if (kw) {
      const hay = ((it.title || "") + " " + (it.text || "")).toLowerCase();
      if (!hay.includes(kw)) return false;
    }
    if (from || to) {
      const d = (it.date || "").slice(0, 10);
      if (!d) return false;                  // exclude undated items if a range is set
      if (from && d < from) return false;
      if (to && d > to) return false;
    }
    return true;
  });
  state.pos = 0;
  $("counter").textContent = state.view.length
    ? `1 / ${state.view.length}` : `0 / 0`;
  render();
}

function go(delta) {
  if (!state.view.length) return;
  state.pos = (state.pos + delta + state.view.length) % state.view.length;
  $("counter").textContent = `${state.pos + 1} / ${state.view.length}`;
  render();
}
function goRandom() {
  if (!state.view.length) return;
  state.pos = Math.floor(Math.random() * state.view.length);
  $("counter").textContent = `${state.pos + 1} / ${state.view.length}`;
  render();
}

function escapeHTML(s) {
  return (s == null ? "" : String(s))
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function render() {
  if (!state.view.length) {
    $("card").innerHTML = `<p class="empty-state">No items match these filters.</p>`;
    return;
  }
  const it = state.view[state.pos];
  const urlHTML = it.url
    ? `<a href="${escapeHTML(it.url)}" target="_blank" rel="noopener noreferrer">↗ open source</a>`
    : `<span style="color:var(--muted)">no public URL</span>`;
  const titleHTML = it.title ? `<div class="card-title">${escapeHTML(it.title)}</div>` : "";
  const metaRows = Object.entries(it.metadata || {})
    .filter(([_, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `<div class="k">${escapeHTML(k)}</div><div class="v">${escapeHTML(v)}</div>`)
    .join("");
  const region = it.regionid ? `· region ${escapeHTML(it.regionid)}` : "";
  $("card").innerHTML = `
    <div class="card-head">
      <span class="src">${escapeHTML(it.source || "—")}</span>
      <span>${escapeHTML(it.date || "(no date)")}</span>
      <span>${region}</span>
      <span class="url-link" style="margin-left:auto">${urlHTML}</span>
    </div>
    ${titleHTML}
    <div class="card-text">${escapeHTML(it.text || "(empty)")}</div>
    ${metaRows ? `<div class="card-meta">${metaRows}</div>` : ""}
  `;
}

async function switchTab(db) {
  state.db = db;
  document.querySelectorAll("#tabs button").forEach(b =>
    b.classList.toggle("active", b.dataset.db === db));
  try { await loadDB(db); } catch (e) {
    $("card").innerHTML = `<p class="empty-state">Could not load ${db}: ${escapeHTML(e.message)}</p>`;
    return;
  }
  rebuildSourceDropdown();
  $("keyword-filter").value = "";
  $("date-from").value = ""; $("date-to").value = "";
  $("source-filter").value = "";
  applyFilters();
  goRandom();
  $("meta").textContent =
    `${cache[db].n_items} items · ${cache[db].n_sources} sources · built ${cache[db].built_at?.slice(0,10) ?? "?"}`;
}

function init() {
  document.querySelectorAll("#tabs button").forEach(b =>
    b.addEventListener("click", () => switchTab(b.dataset.db)));
  ["source-filter","keyword-filter","date-from","date-to"].forEach(id => {
    const el = $(id);
    el.addEventListener("change", applyFilters);
    if (id === "keyword-filter") el.addEventListener("input", () => {
      clearTimeout(window._kwT); window._kwT = setTimeout(applyFilters, 200);
    });
  });
  $("clear-filters").addEventListener("click", () => {
    $("source-filter").value = ""; $("keyword-filter").value = "";
    $("date-from").value = "";     $("date-to").value = "";
    applyFilters();
  });
  $("btn-random").addEventListener("click", goRandom);
  $("btn-prev").addEventListener("click", () => go(-1));
  $("btn-next").addEventListener("click", () => go(1));
  document.addEventListener("keydown", (e) => {
    if (["INPUT","SELECT","TEXTAREA"].includes(document.activeElement?.tagName)) return;
    if (e.code === "Space") { e.preventDefault(); goRandom(); }
    else if (e.code === "ArrowLeft")  go(-1);
    else if (e.code === "ArrowRight") go(1);
  });
  switchTab("telegram");
}

document.addEventListener("DOMContentLoaded", init);
