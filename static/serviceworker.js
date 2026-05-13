// Service Worker for HR System - Offline Capabilities
const CACHE_NAME = 'hr-system-cache-v1';
const OFFLINE_URL = '/offline.html';

// Files to cache for offline functionality
const OFFLINE_VERSION = 1;
const CACHE_NAME = `hr-system-offline-${OFFLINE_VERSION}`;
const OFFLINE_PAGE = 'offline.html';

const urlsToCache = [
  '/',
  '/dashboard',
  '/employees',
  '/leaves',
  '/performance',
  '/payroll',
  '/attendance',
  '/offline.html',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'
];

// Install service worker and cache offline assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service worker: Caching offline assets');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate service worker and clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((cacheName) => {
          return cacheName.startsWith('hr-system-') && cacheName !== CACHE_NAME;
        }).map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache if available, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        // Return cached response if found
        if (cachedResponse) {
          return cachedResponse;
        }

        // Clone the request because it's a one-time use
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest)
          .then((networkResponse) => {
            // Check if we received a valid response
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }

            // Clone the response because it's a one-time use
            const responseToCache = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          })
          .catch(() => {
            // If fetch fails (offline), try to serve the offline page
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_PAGE);
            }
          });
      })
  );
});

// Listen for messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});