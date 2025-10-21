const CACHE_NAME = "cache-update-refresh-v1";
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

function fromCache(request) {
  return caches.open(CACHE_NAME).then((cache) => cache.match(request));
}

function update(request) {
  return caches.open(CACHE_NAME).then((cache) =>
    fetch(request)
      .then((response) => {
        if (isCacheableResponse(response)) {
          cache.put(request, response.clone()).catch((error) => {
            console.warn("[sw] cache put failed", error);
          });
        }
        return response;
      })
      .catch((error) => {
        console.warn("[sw] update failed", error);
        throw error;
      })
  );
}

function refresh(response) {
  if (!response) return undefined;
  return self.clients.matchAll().then((clients) => {
    const message = {
      type: "refresh",
      url: response.url,
      eTag: response.headers.get("ETag"),
    };
    const payload = JSON.stringify(message);
    clients.forEach((client) => client.postMessage(payload));
    return response;
  });
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!shouldHandleFetch(request)) {
    return;
  }

  const updatePromise = update(request);

  event.respondWith(
    fromCache(request)
      .then((cached) => {
        if (cached) return cached;
        return updatePromise.catch(() => fetch(request));
      })
      .catch(() => updatePromise.catch(() => fetch(request)))
      .then((response) => response || caches.match("/index.html"))
  );

  event.waitUntil(updatePromise.then(refresh).catch(() => undefined));
});
