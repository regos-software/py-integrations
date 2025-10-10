const CACHE_NAME = "cache-and-update-v1";
const PRECACHE_ASSETS = [
  "/",
  "/index.html",
  "/assets/app.js",
  "/assets/app.css",
  "/assets/font-awesome.min.css",
  "/assets/icon-192.png",
  "/assets/icon-512.png",
  "/assets/manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .catch((error) => console.warn("[sw] precache failed", error))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((staleKey) => caches.delete(staleKey))
        )
      )
  );
  clients.claim();
});

function shouldHandleFetch(request) {
  if (request.method !== "GET") return false;
  const url = new URL(request.url);
  return url.protocol.startsWith("http") && url.origin === self.location.origin;
}

function isCacheableResponse(response) {
  return (
    response &&
    response.status === 200 &&
    (response.type === "basic" || response.type === "default")
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!shouldHandleFetch(request)) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);

      const updatePromise = fetch(request)
        .then((response) => {
          if (isCacheableResponse(response)) {
            cache.put(request, response.clone());
          }
          return response;
        })
        .catch((error) => {
          console.warn("[sw] network update failed", error);
          return undefined;
        });

      event.waitUntil(updatePromise.catch(() => undefined));

      if (cached) {
        return cached;
      }

      return updatePromise.then((response) => {
        if (response) {
          return response;
        }
        return caches.match("/index.html");
      });
    })
  );
});
