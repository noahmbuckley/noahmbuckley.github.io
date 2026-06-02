/* =============================================================
   Service Worker — offline shell + per-task data precache
   Strategy:
     - install: precache app shell (forced)
     - activate: precache all task data listed in tasks.json (best effort)
     - fetch:    cache-first for our scope; network falls back to cache
   ============================================================= */
const VERSION = 'v9-2026-06-02';
const SHELL_CACHE = 'shell-' + VERSION;
const DATA_CACHE  = 'data-'  + VERSION;

const SHELL_ASSETS = [
  './',
  './index.html',
  './app.js',
  './style.css',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './tasks.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    await cache.addAll(SHELL_ASSETS);
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // Drop old caches
    const keys = await caches.keys();
    await Promise.all(keys.map(k => {
      if (k !== SHELL_CACHE && k !== DATA_CACHE) return caches.delete(k);
    }));
    // Best-effort precache of all task data
    try {
      const reg = await fetch('./tasks.json', { cache: 'no-cache' });
      if (reg.ok) {
        const j = await reg.json();
        const dc = await caches.open(DATA_CACHE);
        const urls = [];
        for (const t of (j.tasks || [])) {
          if (t.schema_url) urls.push(t.schema_url);
          if (t.items_url)  urls.push(t.items_url);
        }
        await Promise.all(urls.map(u =>
          fetch(u, { cache: 'no-cache' })
            .then(r => r.ok && dc.put(u, r.clone()))
            .catch(() => {})
        ));
      }
    } catch (e) { /* offline at activate-time — fine */ }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // only handle requests within our scope
  if (url.origin !== self.location.origin) return;
  if (!url.pathname.startsWith(new URL('./', self.location).pathname)) return;

  event.respondWith((async () => {
    // tasks.json is network-FIRST (with cache fallback) so a freshly-added task
    // list shows up when online WITHOUT needing a service-worker version bump.
    // Everything else stays cache-first (stale-while-revalidate) for offline use.
    if (url.pathname.endsWith('tasks.json')) {
      try {
        const resp = await fetch(req, { cache: 'no-store' });
        if (resp && resp.ok) {
          const cache = await caches.open(SHELL_CACHE);
          try { await cache.put(req, resp.clone()); } catch (e) {}
          return resp;
        }
      } catch (e) { /* offline — fall through to cache */ }
      return (await caches.match(req, { ignoreSearch: true }))
             || new Response('Offline and not cached.', { status: 503 });
    }

    // 1) try caches
    const cached = await caches.match(req, { ignoreSearch: true });
    // 2) network in parallel — update cache if successful
    const net = fetch(req).then(async (resp) => {
      if (resp && resp.ok) {
        const isData = url.pathname.includes('/data/') || url.pathname.endsWith('tasks.json');
        const cache = await caches.open(isData ? DATA_CACHE : SHELL_CACHE);
        try { await cache.put(req, resp.clone()); } catch (e) {}
      }
      return resp;
    }).catch(() => null);

    // Stale-while-revalidate: serve cache if we have it, else wait for network
    return cached || (await net) || new Response('Offline and not cached.', { status: 503 });
  })());
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
