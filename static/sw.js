// Simple Service Worker for Dr. Harmony
// This prevents 404 errors in browser console

self.addEventListener('install', function(event) {
    console.log('Dr. Harmony Service Worker installed');
});

self.addEventListener('fetch', function(event) {
    // Handle requests
    event.respondWith(fetch(event.request));
}); 