// SevaDristi Offline Service Worker — Privacy-Hardened & Versioned
const CACHE_VERSION = 'v1.2.0';
const STATIC_CACHE_NAME = `sevadristi-shell-${CACHE_VERSION}`;

// Only static UI shell assets are permitted to be cached
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== STATIC_CACHE_NAME) {
            console.log('[SW] Purging outdated cache:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Listener for explicit logout/clear commands to enforce zero-leakage privacy
self.addEventListener('message', (event) => {
  if (event.data && (event.data.action === 'CLEAR_CACHE' || event.data.action === 'LOGOUT')) {
    event.waitUntil(
      caches.keys().then((keys) => {
        return Promise.all(
          keys.map((key) => {
            console.log('[SW] User reset requested: Purging cache:', key);
            return caches.delete(key);
          })
        );
      }).then(() => {
        if (event.ports && event.ports[0]) {
          event.ports[0].postMessage({ status: 'CLEARED' });
        }
      })
    );
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // STRICT PRIVACY RULE: Never cache API requests, document uploads, OCR results, metrics, or QR payloads
  if (
    url.pathname.startsWith('/api') || 
    url.pathname.startsWith('/metrics') || 
    url.pathname.startsWith('/health') || 
    event.request.method !== 'GET'
  ) {
    return;
  }

  // Network-first for dynamic scripts, cache fallback for offline app shell
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(STATIC_CACHE_NAME).then((cache) => {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          if (event.request.mode === 'navigate') {
            return caches.match('/index.html');
          }
        });
      })
  );
});
