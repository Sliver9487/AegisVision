const CACHE_NAME = "aegisvision-cache-v1";
const STATIC_ASSETS = [
  "./main.html",
  "./camera.html",
  "./screen.html",
  "./manifest.json",
  "./css/style.css",
  "./css/dashboard.css",
  "./css/camera.css",
  "./css/screen.css",
  "./js/config.js",
  "./js/main.js",
  "./js/camera.js",
  "./js/screen.js",
  "./js/notification.js",
  "./js/websocket.js",
  "./js/api.js",
  "./img/aegisvision.ico"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      await Promise.allSettled(STATIC_ASSETS.map((asset) => cache.add(asset)));
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => (
      Promise.all(cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name)))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET") return;
  if (url.pathname.includes("/analyze_frame") || url.pathname.includes("/events") || url.pathname.includes("/devices") || url.pathname.includes("/health") || url.pathname.includes("/ws")) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
