// State Electric — Service Worker
// Caches app shell for offline use

const CACHE_NAME = 'state-electric-v1';
const OFFLINE_URL = '/offline/';

// Files to cache on install
const PRECACHE_URLS = [
  '/',
  '/dashboard/',
  '/accounts/login/',
  '/static/css/app.css',
  '/static/js/app.js',
  '/manifest.json',
];

// Install — cache app shell
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.filter(function(name) {
          return name !== CACHE_NAME;
        }).map(function(name) {
          return caches.delete(name);
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch — network first, fallback to cache
self.addEventListener('fetch', function(event) {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API calls — let them fail naturally when offline
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    fetch(event.request).then(function(response) {
      // Cache successful responses
      if (response && response.status === 200) {
        var responseClone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, responseClone);
        });
      }
      return response;
    }).catch(function() {
      return caches.match(event.request).then(function(cached) {
        return cached || caches.match(OFFLINE_URL);
      });
    })
  );
});

// Background sync for offline changes
self.addEventListener('sync', function(event) {
  if (event.tag === 'sync-invoices') {
    event.waitUntil(syncInvoices());
  }
  if (event.tag === 'sync-customers') {
    event.waitUntil(syncCustomers());
  }
});

async function syncInvoices() {
  // Triggered when back online — client-side Dexie sync handles the actual data
  const clients = await self.clients.matchAll();
  clients.forEach(function(client) {
    client.postMessage({ type: 'SYNC_INVOICES' });
  });
}

async function syncCustomers() {
  const clients = await self.clients.matchAll();
  clients.forEach(function(client) {
    client.postMessage({ type: 'SYNC_CUSTOMERS' });
  });
}
