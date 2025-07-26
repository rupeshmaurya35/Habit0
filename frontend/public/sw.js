/* Enhanced Service Worker for Smart Reminders PWA - System Notifications & Install Support */

const CACHE_NAME = 'smart-reminders-v3';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png',
  '/apple-touch-icon.png',
  '/favicon.ico'
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

// Enhanced fetch event with network-first strategy for better PWA experience
self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Check if we received a valid response
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        
        // Clone the response for caching
        const responseToCache = response.clone();
        
        caches.open(CACHE_NAME)
          .then((cache) => {
            cache.put(request, responseToCache);
          });
        
        return response;
      })
      .catch(() => {
        // If network fails, try cache
        return caches.match(request);
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
  
  // Handle PWA install event
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
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

// Handle PWA install event
self.addEventListener('appinstalled', (event) => {
  console.log('PWA was installed successfully!');
});

// Background sync for offline reminders (if supported)
self.addEventListener('sync', (event) => {
  console.log('Background sync event:', event.tag);
  if (event.tag === 'reminder-sync') {
    event.waitUntil(
      // Handle background sync for reminders
      Promise.resolve()
    );
  }
});

// Handle push notifications (for future enhancement)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    console.log('Push notification received:', data);
    
    const options = {
      body: data.body || 'Smart Reminder',
      icon: '/icon-192x192.png',
      badge: '/icon-192x192.png',
      tag: 'push-reminder',
      requireInteraction: false,
      data: {
        url: self.location.origin
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Smart Reminders', options)
    );
  }
});