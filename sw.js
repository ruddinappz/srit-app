/* SRITi — service worker (GitHub Pages saja). Membuat pembukaan berikutnya cepat & tahan jaringan buruk.
   - Pustaka (libs/), ikon & logo: cache-dulu.   - index.html, config.js, gas-bridge.js: jaringan-dulu, cadangan cache.
   - Permintaan ke script.google.com / CDN TIDAK disentuh (data selalu langsung dari server). */
const V = 'sriti-1.9.29';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== location.origin) return;
  const cacheFirst = /\/(libs\/|icon-|apple-touch|favicon|logo)/.test(u.pathname);
  if (cacheFirst) {
    e.respondWith(caches.match(r).then(h => h || fetch(r).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(V).then(ca => ca.put(r, c)); }
      return res;
    })));
    return;
  }
  e.respondWith(fetch(r).then(res => {
    if (res.ok) { const c = res.clone(); caches.open(V).then(ca => ca.put(r, c)); }
    return res;
  }).catch(() => caches.match(r).then(h => h || (r.mode === 'navigate' ? caches.match('./index.html') || caches.match('./') : undefined))));
});
