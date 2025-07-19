// Tree Service Estimator Pro - Service Worker
// Version: 1.0.0

const CACHE_NAME = 'tree-service-v1';
const API_CACHE = 'tree-service-api-v1';
const IMAGE_CACHE = 'tree-service-images-v1';

// Files to cache immediately
const STATIC_CACHE_URLS = [
  '/mobile_app/',
  '/mobile_app/index.html',
  '/mobile_app/manifest.json',
  '/mobile_app/css/styles.css',
  '/mobile_app/css/mobile.css',
  '/mobile_app/js/app.js',
  '/mobile_app/js/auth.js',
  '/mobile_app/js/api.js',
  '/mobile_app/js/estimates.js',
  '/mobile_app/js/camera.js',
  '/mobile_app/js/offline.js',
  '/mobile_app/js/utils.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.ttf'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching static assets...');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('Service Worker installed successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Cache installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== API_CACHE && 
                cacheName !== IMAGE_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle image requests
  if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
    return;
  }

  // Handle static assets
  event.respondWith(
    caches.match(request)
      .then(response => {
        if (response) {
          // Return cached version
          return response;
        }

        // Fetch from network
        return fetch(request)
          .then(response => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Return offline page if available
            if (request.destination === 'document') {
              return caches.match('/mobile_app/offline.html');
            }
          });
      })
  );
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // Add header to indicate cached response
      const headers = new Headers(cachedResponse.headers);
      headers.set('X-From-Cache', 'true');
      
      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: headers
      });
    }
    
    // Return error response
    return new Response(
      JSON.stringify({
        error: 'Network error',
        message: 'No network connection and no cached data available'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle image requests with cache-first strategy
async function handleImageRequest(request) {
  const cache = await caches.open(IMAGE_CACHE);
  
  // Try cache first
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Fetch from network
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Return placeholder image if available
    return caches.match('/mobile_app/images/placeholder.png');
  }
}

// Background sync for offline estimates
self.addEventListener('sync', event => {
  if (event.tag === 'sync-estimates') {
    event.waitUntil(syncEstimates());
  }
});

// Sync offline estimates when connection is restored
async function syncEstimates() {
  try {
    // Get all pending estimates from IndexedDB
    const pendingEstimates = await getPendingEstimates();
    
    if (pendingEstimates.length === 0) {
      return;
    }
    
    console.log(`Syncing ${pendingEstimates.length} pending estimates...`);
    
    // Send each estimate to the server
    for (const estimate of pendingEstimates) {
      try {
        const response = await fetch('/api/estimates', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${estimate.token}`
          },
          body: JSON.stringify(estimate.data)
        });
        
        if (response.ok) {
          // Remove from pending queue
          await removePendingEstimate(estimate.id);
          
          // Notify client
          await notifyClients('estimate-synced', {
            localId: estimate.id,
            serverId: (await response.json()).id
          });
        }
      } catch (error) {
        console.error('Failed to sync estimate:', estimate.id, error);
      }
    }
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// Get pending estimates from IndexedDB
async function getPendingEstimates() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TreeServiceDB', 1);
    
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['pendingEstimates'], 'readonly');
      const store = transaction.objectStore('pendingEstimates');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = () => {
        resolve(getAllRequest.result || []);
      };
      
      getAllRequest.onerror = () => {
        reject(getAllRequest.error);
      };
    };
    
    request.onerror = () => {
      reject(request.error);
    };
  });
}

// Remove synced estimate from pending queue
async function removePendingEstimate(id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TreeServiceDB', 1);
    
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['pendingEstimates'], 'readwrite');
      const store = transaction.objectStore('pendingEstimates');
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => {
        resolve();
      };
      
      deleteRequest.onerror = () => {
        reject(deleteRequest.error);
      };
    };
    
    request.onerror = () => {
      reject(request.error);
    };
  });
}

// Notify all clients of an event
async function notifyClients(event, data) {
  const clients = await self.clients.matchAll();
  
  clients.forEach(client => {
    client.postMessage({
      type: event,
      data: data
    });
  });
}

// Handle push notifications
self.addEventListener('push', event => {
  if (!event.data) {
    return;
  }
  
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/mobile_app/images/icons/icon-192x192.png',
    badge: '/mobile_app/images/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data,
    actions: data.actions || []
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  const data = event.notification.data;
  let url = '/mobile_app/';
  
  if (data && data.url) {
    url = data.url;
  }
  
  event.waitUntil(
    clients.openWindow(url)
  );
});

// Message handler for client communication
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then(cache => cache.addAll(event.data.urls))
    );
  }
});