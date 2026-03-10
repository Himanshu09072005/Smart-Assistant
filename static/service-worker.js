const CACHE_NAME = "ai-assistant-cache-v1";

const urlsToCache = [
"/",
"/static/manifest.json",
"/static/icon-192.png",
"/static/icon-512.png"
];

self.addEventListener("install", event => {

console.log("Service Worker Installed");

event.waitUntil(
caches.open(CACHE_NAME)
.then(cache => {
return cache.addAll(urlsToCache);
})
);

});

self.addEventListener("fetch", event => {

event.respondWith(

caches.match(event.request)
.then(response => {

if(response){
return response;
}

return fetch(event.request);

})

);

});