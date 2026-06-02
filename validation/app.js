/* =============================================================
   Validation app — vanilla JS, single file
   - IndexedDB for items / answers / progress
   - Service worker for offline shell
   - Web Share API on iOS, <a download> on Mac
   ============================================================= */

const TASKS_URL  = 'tasks.json';
const DB_NAME    = 'validation';
const DB_VERSION = 1;
const STORE_TASKS    = 'tasks';     // task_id => {schema, items, fetched_at}
const STORE_ANSWERS  = 'answers';   // [task_id, item_id] => {answer, ts}
const STORE_PROGRESS = 'progress';  // task_id => {currentIndex, lastTouched}

/* ============================================================ */
/* IndexedDB minimal wrapper                                    */
/* ============================================================ */
let _dbp = null;
function db() {
  if (_dbp) return _dbp;
  _dbp = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const d = req.result;
      if (!d.objectStoreNames.contains(STORE_TASKS))    d.createObjectStore(STORE_TASKS,    { keyPath: 'task_id' });
      if (!d.objectStoreNames.contains(STORE_ANSWERS))  d.createObjectStore(STORE_ANSWERS,  { keyPath: ['task_id','item_id'] });
      if (!d.objectStoreNames.contains(STORE_PROGRESS)) d.createObjectStore(STORE_PROGRESS, { keyPath: 'task_id' });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return _dbp;
}
async function idbGet(store, key) {
  const d = await db();
  return new Promise((res, rej) => {
    const r = d.transaction(store, 'readonly').objectStore(store).get(key);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function idbPut(store, value) {
  const d = await db();
  return new Promise((res, rej) => {
    const r = d.transaction(store, 'readwrite').objectStore(store).put(value);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function idbDelete(store, key) {
  const d = await db();
  return new Promise((res, rej) => {
    const r = d.transaction(store, 'readwrite').objectStore(store).delete(key);
    r.onsuccess = () => res();
    r.onerror = () => rej(r.error);
  });
}
async function idbGetAll(store, range) {
  const d = await db();
  return new Promise((res, rej) => {
    const r = d.transaction(store, 'readonly').objectStore(store).getAll(range);
    r.onsuccess = () => res(r.result || []);
    r.onerror = () => rej(r.error);
  });
}
async function idbClear(store) {
  const d = await db();
  return new Promise((res, rej) => {
    const r = d.transaction(store, 'readwrite').objectStore(store).clear();
    r.onsuccess = () => res();
    r.onerror = () => rej(r.error);
  });
}

/* ============================================================ */
/* Network helpers                                              */
/* ============================================================ */
async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, { cache: 'no-cache', ...opts });
  if (!r.ok) throw new Error(`Fetch ${url}: ${r.status}`);
  return r.json();
}
const isOnline = () => navigator.onLine;

/* ============================================================ */
/* Global state                                                 */
/* ============================================================ */
const state = {
  tasks:        [],   // [{id, name, schema_url, items_url, ...}]
  taskById:     {},
  currentTaskId: null,
  currentTask:   null, // { task_id, schema, items, fetched_at }
  currentIndex:  0,
  answersCache:  {},   // {item_id: answer-object}
};

/* ============================================================ */
/* Init                                                         */
/* ============================================================ */
window.addEventListener('DOMContentLoaded', init);
window.addEventListener('online',  () => toast('Online'));
window.addEventListener('offline', () => toast('Offline — answers still save locally'));

async function init() {
  registerSW();
  bindGlobalUI();
  await ensureTasksLoaded({ allowNetwork: true });
  renderPicker();
}

function registerSW() {
  if (!('serviceWorker' in navigator)) return;
  // updateViaCache:'none' => the browser fetches sw.js bypassing the HTTP cache when
  // checking for updates. Without this, a long Cache-Control on sw.js (Cloudflare
  // serves max-age=14400 = 4h) means iOS Safari keeps seeing the OLD worker and never
  // updates — the recurring "iPad won't refresh" problem.
  navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' })
    .then(reg => {
      reg.update().catch(() => {});                 // force an update check on every launch
      // When a newly-installed worker takes control, reload once so the fresh
      // task list/app shell render. IndexedDB answers persist across reload.
      let reloaded = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (reloaded) return;
        reloaded = true;
        window.location.reload();
      });
    })
    .catch(err => { console.warn('SW register failed:', err); });
}

/* ============================================================ */
/* Tasks loading + caching                                      */
/* ============================================================ */
async function ensureTasksLoaded({ allowNetwork = true, force = false } = {}) {
  // 1) Cached registry
  let cachedRegistry = await idbGet(STORE_TASKS, '__registry__');
  if (cachedRegistry && !force) {
    state.tasks = cachedRegistry.tasks;
  }
  // 2) Try network
  if (allowNetwork && (force || !cachedRegistry)) {
    try {
      const reg = await fetchJSON(TASKS_URL);
      state.tasks = reg.tasks;
      await idbPut(STORE_TASKS, { task_id: '__registry__', tasks: reg.tasks, fetched_at: Date.now() });
    } catch (e) {
      if (!cachedRegistry) {
        toast('Could not load tasks (offline?). Connect to the internet at least once.');
        state.tasks = [];
      }
    }
  }
  state.taskById = {};
  for (const t of state.tasks) state.taskById[t.id] = t;
}

async function syncAllNow() {
  toast('Syncing…');
  await ensureTasksLoaded({ allowNetwork: true, force: true });
  let n = 0;
  for (const t of state.tasks) {
    try {
      const schema = await fetchJSON(t.schema_url);
      const items  = await fetchJSON(t.items_url);
      await idbPut(STORE_TASKS, { task_id: t.id, schema, items, fetched_at: Date.now() });
      n++;
    } catch (e) {
      console.warn('sync task failed:', t.id, e);
    }
  }
  toast(`Synced ${n}/${state.tasks.length} tasks`);
  if (state.currentTaskId) await openTask(state.currentTaskId, { fromSync: true });
  else renderPicker();
}

async function loadTaskData(taskId, { allowNetwork = true } = {}) {
  let cached = await idbGet(STORE_TASKS, taskId);
  const meta = state.taskById[taskId];
  if (!meta) throw new Error('Unknown task: ' + taskId);

  if (allowNetwork && isOnline()) {
    try {
      const schema = await fetchJSON(meta.schema_url);
      const itemsRaw = await fetchJSON(meta.items_url);
      // Newer chunk builders wrap items in {task_id, schema_version, built_at, n_items, items: [...]};
      // older chunks are a plain array. Accept both shapes.
      const items = Array.isArray(itemsRaw)
        ? itemsRaw
        : (itemsRaw && Array.isArray(itemsRaw.items) ? itemsRaw.items : []);
      cached = { task_id: taskId, schema, items, fetched_at: Date.now() };
      await idbPut(STORE_TASKS, cached);
    } catch (e) {
      if (!cached) throw new Error(`Cannot load task ${taskId} (offline + not cached)`);
    }
  }
  if (!cached) throw new Error(`Task ${taskId} not in cache. Connect online to fetch.`);
  // Re-unwrap on cache hit too, in case an older cache entry holds the wrapped object.
  if (cached.items && !Array.isArray(cached.items) && Array.isArray(cached.items.items)) {
    cached.items = cached.items.items;
  }
  return cached;
}

/* ============================================================ */
/* Picker view                                                  */
/* ============================================================ */
let _pickerGen = 0;  // generation counter — older async renders bail if a newer one starts
async function renderPicker() {
  const myGen = ++_pickerGen;
  show('view-picker'); hide('view-item');
  $('task-name').textContent = 'Validation';
  $('progress-text').textContent = '';
  const list = $('task-list');
  list.innerHTML = '';
  if (!state.tasks.length) {
    list.innerHTML = '<p class="muted">No tasks loaded. Connect to the internet and tap Refresh below.</p>';
    return;
  }
  for (const t of state.tasks) {
    const stats = await taskStats(t.id);
    if (myGen !== _pickerGen) return;  // a newer renderPicker has started; abandon this run
    const card = document.createElement('div');
    card.className = 'task-card';
    card.innerHTML = `
      <div class="task-card-title"></div>
      <div class="task-card-meta"></div>
      <div class="task-card-progress"><div class="task-card-progress-fill"></div></div>
      <div class="task-card-meta progress-text"></div>
    `;
    card.querySelector('.task-card-title').textContent = t.name;
    card.querySelector('.task-card-meta').textContent = t.description || '';
    const pct = stats.total ? (stats.answered / stats.total) * 100 : 0;
    card.querySelector('.task-card-progress-fill').style.width = pct.toFixed(1) + '%';
    card.querySelector('.progress-text').textContent =
      stats.total
        ? `${stats.answered}/${stats.total} done (${pct.toFixed(0)}%)${stats.cached ? '' : ' — not yet cached'}`
        : 'tap to load';
    card.addEventListener('click', () => openTask(t.id));
    list.appendChild(card);
  }
}

async function taskStats(taskId) {
  const cached = await idbGet(STORE_TASKS, taskId);
  if (!cached || !cached.items) return { total: 0, answered: 0, cached: false };
  const allAnswers = await idbGetAll(STORE_ANSWERS,
    IDBKeyRange.bound([taskId, ''], [taskId, '￿'])
  );
  return { total: cached.items.length, answered: allAnswers.length, cached: true };
}

/* ============================================================ */
/* Item view                                                    */
/* ============================================================ */
async function openTask(taskId, { fromSync = false } = {}) {
  try {
    const t = await loadTaskData(taskId, { allowNetwork: !fromSync });
    state.currentTaskId = taskId;
    state.currentTask = t;
    // Restore answers cache for this task
    state.answersCache = {};
    const answers = await idbGetAll(STORE_ANSWERS,
      IDBKeyRange.bound([taskId, ''], [taskId, '￿'])
    );
    for (const a of answers) state.answersCache[a.item_id] = a.answer;
    // Restore progress
    const prog = await idbGet(STORE_PROGRESS, taskId);
    state.currentIndex = prog ? Math.min(prog.currentIndex, t.items.length - 1) : 0;
    show('view-item'); hide('view-picker');
    $('task-name').textContent = t.schema.name || taskId;
    renderInstructions();
    renderItem();
  } catch (e) {
    toast(e.message);
  }
}

function renderInstructions() {
  const el = $('task-instructions');
  el.textContent = state.currentTask.schema.instructions || '';
  el.style.display = state.currentTask.schema.instructions ? 'block' : 'none';
}

function currentItem() {
  return state.currentTask.items[state.currentIndex];
}
function currentItemId() {
  const idField = state.currentTask.schema.id_field;
  return String(currentItem()[idField]);
}

function renderItem() {
  const sch = state.currentTask.schema;
  const item = currentItem();
  const total = state.currentTask.items.length;
  $('progress-text').textContent = `${state.currentIndex + 1} / ${total}`;

  // ===== Display card =====
  const dc = $('display-card');
  dc.className = 'card display-card';
  if (sch.row_class_field) {
    const v = String(item[sch.row_class_field]);
    const cls = (sch.row_class_map && sch.row_class_map[v]) || '';
    if (cls) dc.classList.add(cls);
  }
  dc.innerHTML = '';
  for (const f of sch.display) {
    const row = document.createElement('div');
    row.className = 'field-row';
    if (f.highlight === 'llm') row.classList.add('llm');
    const lbl = document.createElement('div');
    lbl.className = 'field-label';
    lbl.textContent = f.label || f.field;
    const val = document.createElement('div');
    val.className = 'field-value ' + (f.format || '');
    let raw = item[f.field];
    if (raw == null || raw === '' || (typeof raw === 'number' && isNaN(raw))) raw = '—';
    val.textContent = String(raw);
    row.appendChild(lbl); row.appendChild(val);
    dc.appendChild(row);
  }

  // ===== Validation form =====
  renderForm();
}

function renderForm() {
  const sch = state.currentTask.schema;
  const itemId = currentItemId();
  const cur = state.answersCache[itemId] || {};
  const f = $('validation-form');
  f.innerHTML = '';

  for (const v of sch.validation) {
    const grp = document.createElement('div');
    grp.className = 'form-group';
    grp.dataset.field = v.field;

    // show_if logic — recomputed every render
    if (v.show_if) {
      let visible = true;
      for (const [k, vals] of Object.entries(v.show_if)) {
        const have = cur[k];
        if (!vals.includes(have)) { visible = false; break; }
      }
      if (!visible) grp.classList.add('hidden');
    }

    const lbl = document.createElement('label');
    lbl.className = 'field-label-major';
    lbl.textContent = v.label + (v.required ? ' *' : '');
    grp.appendChild(lbl);

    if (v.type === 'enum') {
      const wrap = document.createElement('div');
      wrap.className = 'options-row';
      for (const opt of v.options) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'option-btn tone-' + (opt.tone || 'neutral');
        if (cur[v.field] === opt.value) b.classList.add('selected');
        b.innerHTML = `${escapeHTML(opt.label)} <span class="key-hint">${opt.key ? '['+opt.key+']' : ''}</span>`;
        b.addEventListener('click', () => {
          setAnswerField(v.field, opt.value);
          renderForm();   // re-render to update show_if + selection
        });
        wrap.appendChild(b);
      }
      grp.appendChild(wrap);
    } else if (v.type === 'text') {
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.value = cur[v.field] ?? '';
      inp.placeholder = v.placeholder || '';
      inp.addEventListener('input', e => setAnswerField(v.field, e.target.value));
      grp.appendChild(inp);
    } else if (v.type === 'integer' || v.type === 'number') {
      const inp = document.createElement('input');
      inp.type = 'number';
      if (v.type === 'integer') inp.step = '1';
      inp.value = (cur[v.field] ?? '');
      inp.placeholder = v.placeholder || '';
      inp.addEventListener('input', e => {
        const s = e.target.value;
        if (s === '') setAnswerField(v.field, null);
        else setAnswerField(v.field, v.type === 'integer' ? parseInt(s, 10) : parseFloat(s));
      });
      grp.appendChild(inp);
    } else if (v.type === 'textarea') {
      const ta = document.createElement('textarea');
      ta.value = cur[v.field] ?? '';
      ta.placeholder = v.placeholder || '';
      ta.dataset.notesField = '1';
      ta.addEventListener('input', e => setAnswerField(v.field, e.target.value));
      grp.appendChild(ta);
    }
    f.appendChild(grp);
  }
}

function setAnswerField(field, value) {
  const itemId = currentItemId();
  if (!state.answersCache[itemId]) state.answersCache[itemId] = {};
  if (value === null || value === '' || (typeof value === 'number' && isNaN(value))) {
    delete state.answersCache[itemId][field];
  } else {
    state.answersCache[itemId][field] = value;
  }
}

/* ============================================================ */
/* Navigation + save                                            */
/* ============================================================ */
async function persistCurrentAnswer() {
  const taskId = state.currentTaskId;
  const itemId = currentItemId();
  const ans = state.answersCache[itemId];
  if (ans && Object.keys(ans).length > 0) {
    await idbPut(STORE_ANSWERS, {
      task_id: taskId, item_id: itemId,
      answer: ans, ts: new Date().toISOString()
    });
  }
}
async function persistProgress() {
  await idbPut(STORE_PROGRESS, {
    task_id: state.currentTaskId,
    currentIndex: state.currentIndex,
    lastTouched: new Date().toISOString()
  });
}

async function gotoIndex(i) {
  await persistCurrentAnswer();
  const total = state.currentTask.items.length;
  if (i < 0) i = 0;
  if (i >= total) i = total - 1;
  state.currentIndex = i;
  await persistProgress();
  renderItem();
}
async function saveAndNext() {
  await persistCurrentAnswer();
  if (state.currentIndex < state.currentTask.items.length - 1) {
    state.currentIndex++;
    await persistProgress();
    renderItem();
    toast('Saved');
  } else {
    await persistProgress();
    toast('Last item — saved.');
  }
}

/* ============================================================ */
/* Export                                                       */
/* ============================================================ */
// Use Web Share API only on iOS (where <a download> is unreliable inside
// standalone PWAs). Everywhere else — Mac, Android, desktop browsers — use
// the universal <a download> path, which is reliable. iPadOS 13+ reports
// itself as MacIntel + maxTouchPoints>1, so check for that too.
const IS_IOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

async function exportAnswers() {
  const taskId = state.currentTaskId;
  if (!taskId) {
    setMenuMsg('Open a task first, then export.');
    toast('Open a task first');
    return;
  }
  closeMenu();   // close the sheet so the user sees feedback
  try {
    await persistCurrentAnswer();
    const t = state.currentTask;
    const answers = await idbGetAll(STORE_ANSWERS,
      IDBKeyRange.bound([taskId, ''], [taskId, '￿'])
    );
    const idField = t.schema.id_field;
    // Join items + answers; emit one row per item even if unanswered, so reviewers see the universe.
    const items = t.items.map(it => {
      const id = String(it[idField]);
      const a  = answers.find(x => x.item_id === id);
      return {
        [idField]: it[idField],
        answer:   a ? a.answer : null,
        answered_at: a ? a.ts : null
      };
    });
    const payload = {
      task_id: taskId,
      schema_version: t.schema.version || null,
      exported_at: new Date().toISOString(),
      user_agent: navigator.userAgent,
      n_items: t.items.length,
      n_answered: answers.length,
      items
    };
    const fname = `validation_${taskId}_${todayISO()}.json`;
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    await downloadOrShare(blob, fname);
  } catch (e) {
    console.error('export failed:', e);
    toast('Export failed: ' + (e && e.message ? e.message : 'unknown error'));
  }
}

/* ============================================================ */
/* Import — overlay answers from another device's export        */
/* ============================================================ */
// Strategy: per-eventid, last-write-wins by timestamp.
//   - Local has answer A (ts=t_a), import has answer B (ts=t_b)
//     → keep newer one. Ties: imported wins (assume sender is authoritative).
//   - Local has answer, import doesn't → keep local.
//   - Local doesn't, import does → take imported.
async function importAnswersPickFile() {
  const taskId = state.currentTaskId;
  if (!taskId) {
    setMenuMsg('Open a task first, then import.');
    toast('Open a task first');
    return;
  }
  $('import-file').value = '';
  $('import-file').click();
}

async function importAnswersFromFile(file) {
  const taskId = state.currentTaskId;
  if (!taskId || !file) return;
  closeMenu();
  try {
    const text = await file.text();
    const j = JSON.parse(text);
    if (!j || !j.task_id) throw new Error('Not a validation export (missing task_id).');
    if (j.task_id !== taskId) {
      const ok = confirm(
        `This export is for task "${j.task_id}", but you're in "${taskId}".\n\n` +
        `Continue anyway? (Will only import items whose eventid is in the current task.)`
      );
      if (!ok) { toast('Import cancelled.'); return; }
    }
    const items = Array.isArray(j.items) ? j.items : [];
    if (!items.length) { toast('No items in export.'); return; }

    // Build set of valid eventids in current task
    const idField = state.currentTask.schema.id_field;
    const validIds = new Set(state.currentTask.items.map(it => String(it[idField])));

    let kept_newer_local = 0, overwrote_local = 0, net_new = 0, skipped_no_answer = 0, skipped_unknown_id = 0;

    for (const it of items) {
      const eventId = String(it[idField]);
      if (!validIds.has(eventId)) { skipped_unknown_id++; continue; }
      if (!it.answer || Object.keys(it.answer).length === 0) { skipped_no_answer++; continue; }

      const importedTs = it.answered_at || j.exported_at || new Date(0).toISOString();
      const existing = await idbGet(STORE_ANSWERS, [taskId, eventId]);
      if (existing) {
        const localTs = existing.ts || new Date(0).toISOString();
        if (importedTs > localTs) {
          await idbPut(STORE_ANSWERS, {
            task_id: taskId, item_id: eventId,
            answer: it.answer, ts: importedTs
          });
          overwrote_local++;
        } else {
          kept_newer_local++;
        }
      } else {
        await idbPut(STORE_ANSWERS, {
          task_id: taskId, item_id: eventId,
          answer: it.answer, ts: importedTs
        });
        net_new++;
      }
    }

    // Refresh in-memory cache for current task
    state.answersCache = {};
    const all = await idbGetAll(STORE_ANSWERS,
      IDBKeyRange.bound([taskId, ''], [taskId, '￿'])
    );
    for (const a of all) state.answersCache[a.item_id] = a.answer;
    renderItem();

    const summary = [
      `Import complete:`,
      `  ${net_new} new`,
      `  ${overwrote_local} overwrote local (import was newer)`,
      `  ${kept_newer_local} kept local (it was newer)`,
      `  ${skipped_no_answer} skipped (no answer in export)`,
      `  ${skipped_unknown_id} skipped (eventid not in this task)`
    ].join('\n');
    setMenuMsg(summary);
    toast(`Imported: ${net_new} new, ${overwrote_local} updated`);
  } catch (e) {
    console.error('import failed:', e);
    toast('Import failed: ' + (e && e.message ? e.message : 'unknown'));
  }
}

async function downloadOrShare(blob, fname) {
  // On iOS PWAs <a download> is unreliable, so prefer the share sheet.
  if (IS_IOS) {
    try {
      const file = new File([blob], fname, { type: blob.type });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: fname, text: 'Validation export' });
        toast('Shared. Save to Files / Dropbox.');
        return;
      }
    } catch (e) {
      // user cancelled or share threw — fall through to <a download>
    }
  }
  // Universal: trigger a download. Reliable on Mac/Chrome (PWA or tab), Android, etc.
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = fname;
  // Some browsers require the anchor to be in the DOM; some PWA contexts strip it.
  // To handle Chrome-PWA on macOS reliably, use a forced "click" event.
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { try { a.remove(); URL.revokeObjectURL(url); } catch(e){} }, 1500);
  toast('Downloaded ' + fname);
}

/* ============================================================ */
/* Storage / persistence                                        */
/* ============================================================ */
async function requestPersistent() {
  if (!navigator.storage || !navigator.storage.persist) {
    setMenuMsg('navigator.storage.persist not supported');
    return;
  }
  const already = await navigator.storage.persisted();
  if (already) { setMenuMsg('Storage already persistent. ✓'); return; }
  const ok = await navigator.storage.persist();
  setMenuMsg(ok ? 'Storage now persistent. ✓' : 'Browser refused — storage may be evicted under pressure.');
}
async function showStorageInfo() {
  if (!navigator.storage || !navigator.storage.estimate) {
    setMenuMsg('Storage estimate unavailable.');
    return;
  }
  const est = await navigator.storage.estimate();
  const persisted = await (navigator.storage.persisted ? navigator.storage.persisted() : false);
  const used = (est.usage / 1024 / 1024).toFixed(1);
  const quota = (est.quota / 1024 / 1024).toFixed(0);
  setMenuMsg(`Used ${used} MB / ${quota} MB · persistent: ${persisted ? 'yes' : 'no'} · online: ${isOnline() ? 'yes' : 'no'}`);
}

/* ============================================================ */
/* Stats                                                        */
/* ============================================================ */
async function showTaskStats() {
  const taskId = state.currentTaskId; if (!taskId) return;
  const t = state.currentTask;
  const answers = await idbGetAll(STORE_ANSWERS,
    IDBKeyRange.bound([taskId, ''], [taskId, '￿'])
  );
  // Tally verdicts and per-strata if available
  const verdicts = {};
  for (const a of answers) {
    const v = a.answer && a.answer.verdict;
    if (v) verdicts[v] = (verdicts[v] || 0) + 1;
  }
  const lines = [
    `Total items: ${t.items.length}`,
    `Answered:    ${answers.length}`,
    `Remaining:   ${t.items.length - answers.length}`,
    '',
    'Verdicts:',
    ...Object.entries(verdicts).sort().map(([k, n]) => `  ${k}: ${n}`)
  ];
  setMenuMsg(lines.join('\n'));
}

/* ============================================================ */
/* Reset                                                        */
/* ============================================================ */
async function resetCurrentTask() {
  if (!state.currentTaskId) return;
  if (!confirm(`Wipe ALL answers for task "${state.currentTask.schema.name}"?\n\nThis cannot be undone. Export first if you want a backup.`)) return;
  const taskId = state.currentTaskId;
  // Delete all answers for this task
  const d = await db();
  await new Promise((res, rej) => {
    const tx = d.transaction(STORE_ANSWERS, 'readwrite');
    const store = tx.objectStore(STORE_ANSWERS);
    const range = IDBKeyRange.bound([taskId, ''], [taskId, '￿']);
    const req = store.openCursor(range);
    req.onsuccess = e => {
      const c = e.target.result;
      if (c) { c.delete(); c.continue(); }
      else res();
    };
    req.onerror = () => rej(req.error);
  });
  await idbDelete(STORE_PROGRESS, taskId);
  state.answersCache = {};
  state.currentIndex = 0;
  toast('Task reset.');
  renderItem();
}
async function resetAll() {
  if (!confirm('Wipe ALL local data: answers, progress, cached tasks?\n\nCannot be undone.')) return;
  await idbClear(STORE_ANSWERS);
  await idbClear(STORE_PROGRESS);
  await idbClear(STORE_TASKS);
  toast('All local data wiped. Reloading…');
  setTimeout(() => location.reload(), 600);
}

/* ============================================================ */
/* UI binding                                                   */
/* ============================================================ */
function bindGlobalUI() {
  $('btn-home').addEventListener('click', async () => {
    if (state.currentTaskId) await persistCurrentAnswer();
    state.currentTaskId = null; state.currentTask = null;
    renderPicker();
  });
  $('btn-menu').addEventListener('click', () => {
    setMenuMsg('');
    show('menu-sheet'); $('menu-sheet').setAttribute('aria-hidden', 'false');
  });
  $('btn-close-menu').addEventListener('click', closeMenu);
  $('menu-sheet').addEventListener('click', e => {
    if (e.target.id === 'menu-sheet') closeMenu();
  });

  $('btn-prev').addEventListener('click', () => gotoIndex(state.currentIndex - 1));
  $('btn-skip').addEventListener('click', () => gotoIndex(state.currentIndex + 1));
  $('btn-jump').addEventListener('click', async () => {
    const total = state.currentTask.items.length;
    const v = prompt(`Jump to row (1–${total}):`, state.currentIndex + 1);
    if (!v) return;
    const i = parseInt(v, 10) - 1;
    if (!isNaN(i)) gotoIndex(i);
  });
  $('btn-save-next').addEventListener('click', saveAndNext);

  $('btn-refresh-tasks').addEventListener('click', () => syncAllNow());
  $('btn-export').addEventListener('click',     exportAnswers);
  $('btn-import').addEventListener('click',     importAnswersPickFile);
  $('import-file').addEventListener('change',   e => {
    const f = e.target.files && e.target.files[0];
    if (f) importAnswersFromFile(f);
  });
  $('btn-stats').addEventListener('click',      showTaskStats);
  $('btn-go-picker').addEventListener('click',  () => { closeMenu(); $('btn-home').click(); });
  $('btn-sync-now').addEventListener('click',   syncAllNow);
  $('btn-persist').addEventListener('click',    requestPersistent);
  $('btn-storage-info').addEventListener('click', showStorageInfo);
  $('btn-reset-task').addEventListener('click', resetCurrentTask);
  $('btn-reset-all').addEventListener('click',  resetAll);

  // Keyboard shortcuts (item view only)
  document.addEventListener('keydown', e => {
    if (!state.currentTask) return;
    if ($('view-item').classList.contains('hidden')) return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea') {
      // In a text input, only handle a couple of overrides
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    if (e.key === 'ArrowRight')      { e.preventDefault(); gotoIndex(state.currentIndex + 1); }
    else if (e.key === 'ArrowLeft')  { e.preventDefault(); gotoIndex(state.currentIndex - 1); }
    else if (e.key === 'Enter')      { e.preventDefault(); saveAndNext(); }
    else if (e.key.toLowerCase() === 'n') {
      const ta = document.querySelector('textarea[data-notes-field]');
      if (ta) { e.preventDefault(); ta.focus(); }
    }
    else if (['1','2','3','4','5','6','7','8','9'].includes(e.key)) {
      // verdict (or first enum) shortcut — find enum group with matching key
      const sch = state.currentTask.schema;
      for (const v of sch.validation) {
        if (v.type !== 'enum') continue;
        const opt = v.options.find(o => o.key === e.key);
        if (opt) {
          // only if this group is currently visible
          const grp = document.querySelector(`.form-group[data-field="${v.field}"]`);
          if (grp && !grp.classList.contains('hidden')) {
            e.preventDefault();
            setAnswerField(v.field, opt.value);
            renderForm();
            break;
          }
        }
      }
    }
  });
}

function closeMenu() {
  hide('menu-sheet'); $('menu-sheet').setAttribute('aria-hidden', 'true');
}
function setMenuMsg(s) {
  const el = $('menu-msg');
  el.textContent = s; el.style.whiteSpace = 'pre-wrap';
}

/* ============================================================ */
/* Misc helpers                                                 */
/* ============================================================ */
function $(id) { return document.getElementById(id); }
function show(id) { $(id).classList.remove('hidden'); }
function hide(id) { $(id).classList.add('hidden'); }
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
function todayISO() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;
}
let _toastT;
function toast(msg) {
  const el = $('toast');
  el.textContent = msg;
  show('toast');
  clearTimeout(_toastT);
  _toastT = setTimeout(() => hide('toast'), 1800);
}
