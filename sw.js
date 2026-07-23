/* Service Worker — Кондитерская фабрика «Восток» (PWA) */
const VERSION = "vostok-v5";
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;

// App shell — то, что нужно для запуска офлайн.
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./src/main.js",
  "./src/products-data.js",
  "./manifest.webmanifest",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/apple-touch-icon.png",
];

const isShellAsset = (pathname) =>
  /\.(?:html|css|js|webmanifest)$/i.test(pathname) || pathname.endsWith("/");

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
      .catch(() => {})
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Навигация и shell (html/css/js): сеть первая, иначе обновления не доезжают.
  if (request.mode === "navigate" || isShellAsset(url.pathname)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === "basic") {
            const copy = response.clone();
            const key = request.mode === "navigate" ? "./index.html" : request;
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(key, copy));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match("./index.html"))
        )
    );
    return;
  }

  // Картинки и прочее: stale-while-revalidate.
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === "basic") {
            const copy = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
