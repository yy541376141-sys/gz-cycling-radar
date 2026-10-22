/**
 * Service Worker: 骑行巡航雷达 PWA 离线缓存引擎
 * 版本: v1.2.0
 * 策略:
 *  - 核心静态资源 (App Shell): Stale-While-Revalidate (瞬时离线启动 + 自动后台热更)
 *  - CDN 库资源 (Leaflet 等): Cache-First (永久缓存优先)
 *  - 地图瓦片 (CartoDB / OSM / AMap): Cache-First + LRU 最大容量淘汰 (1500瓦片) + 离线兜底雷达网格
 */

const STATIC_CACHE = 'rider-radar-static-v1.2';
const TILE_CACHE = 'rider-radar-tiles-v1.2';
const MAX_TILES = 1500; // 防止 iOS WebKit 存储配额超出

// 离线核心白名单
const PRECACHE_ASSETS = [
  './',
  './rider_radar.html',
  './index.html',
  './manifest.json',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/safari-pinned-tab.svg',
  'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css',
  'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js',
  'https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.css',
  'https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css',
  'https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js'
];

// 离线无瓦片时返回的高科技雷达网格占位 SVG
const OFFLINE_TILE_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="#0b0f19"/>
  <path d="M0 0h256v256H0z" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
  <line x1="0" y1="128" x2="256" y2="128" stroke="rgba(0,242,254,0.15)" stroke-width="1" stroke-dasharray="4 4"/>
  <line x1="128" y1="0" x2="128" y2="256" stroke="rgba(0,242,254,0.15)" stroke-width="1" stroke-dasharray="4 4"/>
  <circle cx="128" cy="128" r="32" fill="none" stroke="rgba(0,242,254,0.12)" stroke-width="1"/>
  <circle cx="128" cy="128" r="3" fill="#00f2fe" opacity="0.4"/>
  <text x="128" y="142" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="rgba(148,163,184,0.6)" text-anchor="middle">离线未缓存瓦片</text>
</svg>`.trim();

// 安装事件：快速完成静态资源预缓存并跳过等待
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      // 容错预缓存：即便个别资源拉取失败也不阻塞安装
      return Promise.allSettled(
        PRECACHE_ASSETS.map((url) =>
          cache.add(new Request(url, { cache: 'reload' })).catch((err) => {
            console.warn('[SW] Precache failed for:', url, err);
          })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// 激活事件：接管客户端，清理历史过期缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== STATIC_CACHE && key !== TILE_CACHE) {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 判断是否为地图瓦片请求
function isTileRequest(url) {
  return (
    url.includes('cartocdn.com') ||
    url.includes('tile.openstreetmap.org') ||
    url.includes('amap.com') ||
    url.includes('tianditu.gov.cn') ||
    /\/tiles?\/\d+\/\d+\/\d+/.test(url)
  );
}

// LRU 瓦片数量限制，避免 iOS 50MB 磁盘配额满额
async function trimTileCache(cache) {
  const keys = await cache.keys();
  if (keys.length > MAX_TILES) {
    const toDeleteCount = keys.length - MAX_TILES + 100; // 一次淘汰100张最旧的
    for (let i = 0; i < toDeleteCount; i++) {
      await cache.delete(keys[i]);
    }
  }
}

// 拦截请求并执行分流缓存策略
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = request.url;

  // 1. 只处理 GET 请求
  if (request.method !== 'GET') return;

  // 2. 地图瓦片：Cache-First + 离线兜底
  if (isTileRequest(url)) {
    event.respondWith(
      caches.open(TILE_CACHE).then(async (cache) => {
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
          return cachedResponse;
        }

        try {
          const networkResponse = await fetch(request);
          if (networkResponse && networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
            trimTileCache(cache).catch(() => {});
          }
          return networkResponse;
        } catch (err) {
          // 离线无信号且无缓存，返回高科技网格 SVG 瓦片，避免地图出现灰色碎图
          return new Response(OFFLINE_TILE_SVG, {
            status: 200,
            headers: {
              'Content-Type': 'image/svg+xml;charset=utf-8',
              'Cache-Control': 'public, max-age=86400'
            }
          });
        }
      })
    );
    return;
  }

  // 3. CDN JS/CSS 静态库：Cache-First
  if (url.includes('cdn.jsdelivr.net') || url.includes('/icons/')) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;
        try {
          const networkResp = await fetch(request);
          if (networkResp.status === 200) {
            cache.put(request, networkResp.clone());
          }
          return networkResp;
        } catch (e) {
          return cached || new Response('Offline CDN Asset Not Found', { status: 503 });
        }
      })
    );
    return;
  }

  // 4. HTML 及其他 App Shell 资源：Stale-While-Revalidate
  event.respondWith(
    caches.open(STATIC_CACHE).then(async (cache) => {
      const cachedResponse = await cache.match(request);

      const fetchPromise = fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
          }
          return networkResponse;
        })
        .catch(() => {
          // 离线且如果是页面导航请求，返回缓存的 HTML
          if (request.mode === 'navigate' || request.destination === 'document') {
            return cache.match('./rider_radar.html') || cachedResponse;
          }
          return cachedResponse;
        });

      return cachedResponse || fetchPromise;
    })
  );
});

// 监听指令消息（如清除瓦片缓存）
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data === 'CLEAR_TILES') {
    caches.delete(TILE_CACHE).then(() => {
      console.log('[SW] Tile cache cleared on user demand.');
    });
  }
});
