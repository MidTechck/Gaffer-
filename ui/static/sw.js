self.addEventListener("install", function (e) {
  e.waitUntil(caches.open("ml26-v1").then(function (c) {
    return c.addAll(["/static/css/app.css", "/static/js/desk.js", "/static/js/plan.js", "/static/img/icon-192.png"]);
  }));
  self.skipWaiting();
});
self.addEventListener("activate", function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request).catch(function () { return caches.match(e.request); }));
});
