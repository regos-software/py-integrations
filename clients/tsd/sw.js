const CACHE = 'tsd-v1';
const PRECACHE = [
  '/apps/tsd/',
  '/apps/tsd/index.html',
  '/apps/tsd/manifest.webmanifest',
  '/apps/tsd/assets/app.css'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
});
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request))
  );
});
