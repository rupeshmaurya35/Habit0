/* Service Worker for Smart Reminders PWA - System Notifications */

const CACHE_NAME = 'smart-reminders-v2';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png'
];

// Install service worker
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        // Force the waiting service worker to become the active service worker
        return self.skipWaiting();
      })
  );
});

// Activate service worker
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Ensure the service worker takes control immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

// Handle messages from main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);
  
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body, tag } = event.data;
    
    // Show system notification (appears in notification bar)
    self.registration.showNotification(title, {
      body: body,
      icon: '/icon-192x192.png',
      badge: '/icon-192x192.png',
      tag: tag || 'reminder',
      requireInteraction: false,
      silent: false,
      timestamp: Date.now(),
      data: {
        url: self.location.origin,
        dismissTime: Date.now() + 10000 // Auto dismiss after 10 seconds
      },
      actions: [
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    }).then(() => {
      console.log('System notification shown');
      
      // Auto dismiss after 10 seconds
      setTimeout(() => {
        self.registration.getNotifications({ tag: tag || 'reminder' })
          .then(notifications => {
            notifications.forEach(notification => {
              if (notification.data && Date.now() >= notification.data.dismissTime) {
                notification.close();
                console.log('Notification auto-dismissed');
              }
            });
          });
      }, 10000);
    }).catch(error => {
      console.error('Error showing notification:', error);
    });
  }
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.notification);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    // Just close the notification
    return;
  }
  
  // Focus or open the app window
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Try to focus existing window
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if no existing window found
        if (self.clients.openWindow) {
          return self.clients.openWindow(self.location.origin);
        }
      })
  );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event.notification);
});