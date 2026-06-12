/* Zeus – Service Worker: macht die App offline-fähig.
   Audio: Cache-first (unveränderlich). Rest: Netz zuerst, Cache als Fallback. */
const CACHE = 'zeus-v2';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
    await clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/')) return;   // Foto-Import nie cachen

  if (url.pathname.includes('/data/audio/')) {
    // Audiodateien ändern sich nicht: Cache zuerst
    e.respondWith((async () => {
      const c = await caches.open(CACHE);
      const hit = await c.match(e.request);
      if (hit) return hit;
      const r = await fetch(e.request);
      if (r.ok) c.put(e.request, r.clone());
      return r;
    })());
    return;
  }

  // App-Code & Daten: Netz zuerst (Updates kommen durch), offline aus dem Cache
  e.respondWith((async () => {
    try {
      const r = await fetch(e.request);
      if (r.ok) {
        const kopie = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, kopie));
      }
      return r;
    } catch {
      const hit = await caches.match(e.request, { ignoreSearch: true });
      if (hit) return hit;
      if (e.request.mode === 'navigate')
        return (await caches.match('./', { ignoreSearch: true })) || Response.error();
      return Response.error();
    }
  })());
});
