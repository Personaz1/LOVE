// Simple Service Worker for ΔΣ Guardian
// This prevents 404 errors in browser console

self.addEventListener('install', function(event) {
    console.log('ΔΣ Guardian Service Worker installed');
});

self.addEventListener('fetch', function(event) {
    // Handle requests
    event.respondWith(fetch(event.request));
}); 