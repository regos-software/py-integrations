// sw.js
const VERSION = '2025-10-06';
const PRECACHE = `tsd-precache-v3-${VERSION}`;
const RUNTIME  = `tsd-runtime-v3-${VERSION}`;

// Важно: у вас в HTML ресурсы идут с query (?assets=..., ?pwa=manifest)
// поэтому именно их и кладём в предкэш относительно scope SW.
const PRECACHE_URLS = [
  './',                 // shell
  'index.html',         // SPA entry
  '?pwa=manifest',
  '?assets=app.css',
  '?assets=app.js',
  '?assets=icon-192.png',
  '?assets=icon-512.png'
];

// ---------- install ----------
self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(PRECACHE);
    await cache.addAll(PRECACHE_URLS);
    // моментально активируем новую версию
    self.skipWaiting();
  })());
});

// ---------- activate ----------
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // удаляем старые версии кэшей
    const names = await caches.keys();
    await Promise.all(
      names
        .filter((n) => n !== PRECACHE && n !== RUNTIME)
        .map((n) => caches.delete(n))
    );
    // навигационный preload быстрее first paint
    try { await self.registration.navigationPreload.enable(); } catch {}
    await self.clients.claim();
  })());
});

// ---------- helpers ----------
async function staleWhileRevalidate(request, cacheName = RUNTIME) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((resp) => {
      // Оpaque (cross-origin no-cors) тоже можно кэшировать
      if (resp && (resp.ok || resp.type === 'opaque')) {
        cache.put(request, resp.clone()).catch(() => {});
      }
      return resp;
    })
    .catch(() => undefined);
  return cached || networkPromise || new Response('', { status: 504 });
}

// ---------- fetch ----------
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // только GET
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;

  // SPA навигация: offline fallback на index.html
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        // если включён navigationPreload
        const preload = await event.preloadResponse;
        if (preload) return preload;
        return await fetch(req);
      } catch {
        const cache = await caches.open(PRECACHE);
        const fallback = await cache.match('index.html');
        return fallback || new Response('Offline', { status: 503 });
      }
    })());
    return;
  }

  // Для ваших динамических ресурсов (?assets=...) — SWR
  if (sameOrigin && url.searchParams.has('assets')) {
    event.respondWith(staleWhileRevalidate(req));
    return;
  }

  // Для заранее предкэшированных — cache-first
  if (sameOrigin) {
    event.respondWith((async () => {
      const hit = await caches.match(req);
      return hit || fetch(req);
    })());
    return;
  }

  // Внешние статики (иконки, css/js с CDN) — SWR, остальное — сеть
  const isStaticExt = /\.(?:css|js|woff2?|png|jpg|jpeg|svg|gif|ico)$/.test(url.pathname);
  if (isStaticExt) {
    event.respondWith(staleWhileRevalidate(req));
  } else {
    event.respondWith(fetch(req));
  }
});
