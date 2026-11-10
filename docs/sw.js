/* Offline support for the News Desk app.
   The page itself is cached so the app opens without a connection.
   news.json is always fetched fresh first; the last copy is used only when offline. */
const CACHE = "iir-shell-v10";
const SHELL = ["./", "index.html", "post.html", "manifest.webmanifest", "icon-192.png", "icon-512.png"];
const NEWS_KEY = "news.json";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((c) =>
        c.addAll(SHELL).then(() =>
          // also keep a first copy of the headlines, so the very first offline start has something to show
          fetch(NEWS_KEY, { cache: "no-store" }).then((r) => (r.ok ? c.put(NEWS_KEY, r) : null)).catch(() => null)
        )
      )
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("iir-") && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // fonts and outlet links go straight to the network

  if (url.pathname.endsWith("/news.json")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(NEWS_KEY, copy)); }
          return res;
        })
        .catch(() => caches.match(NEWS_KEY).then((hit) => hit || Response.error()))
    );
    return;
  }

  // App files: show the saved copy at once, refresh it in the background.
  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      const net = fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
          return res;
        })
        .catch(() => hit);
      return hit || net;
    })
  );
});
