/* Appuscholar service worker. Keeps the app and its libraries so it opens with no connection.
   Same-origin files: network first, so a new upload reaches online students at once; the saved copy
   is used only when the network fails. Library and font files: saved copy first.
   AI providers, paper search and every other site are never touched. */
const VER = 'appu-v75-2026.10.17d';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
const LIBS = [
  'https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/pptxgenjs/3.12.0/pptxgen.bundle.js'
];
const ASSETS = ["./assets/bg_class.webp", "./assets/face_raj_m0.webp", "./assets/face_raj_m1.webp", "./assets/face_raj_m2.webp", "./assets/face_raj_m3.webp", "./assets/face_raj_m4.webp", "./assets/face_raj_m5.webp", "./assets/face_raj_m6.webp", "./assets/ch_appu_explain.webp", "./assets/ch_appu_point.webp", "./assets/ch_appu_stand.webp", "./assets/ch_appu_talk.webp", "./assets/ch_appu_warn.webp", "./assets/ch_meera_explain.webp", "./assets/ch_meera_happy.webp", "./assets/ch_meera_point.webp", "./assets/ch_meera_stand.webp", "./assets/ch_meera_talk.webp", "./assets/ch_meera_think.webp", "./assets/ch_meera_warn.webp", "./assets/ch_raj_explain.webp", "./assets/ch_raj_happy.webp", "./assets/ch_raj_point.webp", "./assets/ch_raj_stand.webp", "./assets/ch_raj_talk.webp", "./assets/ch_raj_think.webp", "./assets/ch_raj_warn.webp", "./assets/face_appu_c.webp", "./assets/face_appu_o.webp", "./assets/face_meera_c.webp", "./assets/face_meera_o.webp", "./assets/face_raj_c.webp", "./assets/face_raj_o.webp", "./assets/pt_einstein.webp", "./assets/pt_kalam.webp", "./assets/pt_raman.webp"];
const LIB_HOSTS = ['cdnjs.cloudflare.com', 'fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(VER);
    await Promise.all(SHELL.concat(LIBS, ASSETS).map(u => c.add(u).catch(() => {})));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== VER && k.indexOf('appu-') === 0).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    if (url.pathname.endsWith('/sw.js')) return;
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res && res.ok) { const c = await caches.open(VER); c.put(req, res.clone()).catch(() => {}); }
        return res;
      } catch (err) {
        const hit = await caches.match(req, { ignoreSearch: true });
        if (hit) return hit;
        if (req.mode === 'navigate') { const shell = await caches.match('./index.html'); if (shell) return shell; }
        throw err;
      }
    })());
    return;
  }
  if (LIB_HOSTS.indexOf(url.hostname) >= 0) {
    e.respondWith((async () => {
      const hit = await caches.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res && (res.ok || res.type === 'opaque')) { const c = await caches.open(VER); c.put(req, res.clone()).catch(() => {}); }
      return res;
    })());
  }
});
