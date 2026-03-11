const CACHE_NAME = "smart-assistant-cache-v1";

const urlsToCache = [
  "/",
  "/static/manifest.json",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "https://cdn.jsdelivr.net/npm/marked/marked.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});