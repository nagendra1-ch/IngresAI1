import axios from 'axios';

// Connect to FastAPI server running on port 8000 in dev, or use relative URLs in production
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Lightweight in-memory client-side cache for GET requests
const requestCache = new Map();
const CACHE_TTL_MS = 180000; // 3 minutes

export const clearClientCache = () => {
  requestCache.clear();
};

// Request interceptor to attach JWT token and check client cache
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ingres_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Invalidate client cache on modifying requests
    if (config.method && config.method.toLowerCase() !== 'get') {
      requestCache.clear();
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add custom cached get helper
const originalGet = api.get;
api.get = function (url, config = {}) {
  const cacheKey = `${url}_${JSON.stringify(config.params || {})}`;
  const cached = requestCache.get(cacheKey);
  const now = Date.now();

  // Certain frequently accessed and slowly mutating endpoints benefit heavily from client caching
  const cacheableEndpoints = [
    '/api/districts',
    '/api/districts/map',
    '/api/dashboard/summary',
    '/api/dashboard/state-statistics',
    '/api/dashboard/district-statistics',
    '/api/dashboard/rainfall',
    '/api/dashboard/groundwater'
  ];

  const isCacheable = cacheableEndpoints.some(ep => url.startsWith(ep));

  if (isCacheable && cached && (now - cached.timestamp < CACHE_TTL_MS)) {
    return Promise.resolve({ data: JSON.parse(JSON.stringify(cached.data)), status: 200, statusText: 'OK', fromCache: true });
  }

  return originalGet.call(this, url, config).then((response) => {
    if (isCacheable && response && response.status === 200) {
      requestCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      });
    }
    return response;
  });
};

// Response interceptor to catch unauthorized errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if error is 401 Unauthorized (session expired / invalid token)
    if (error.response && error.response.status === 401) {
      const path = window.location.pathname;
      if (path !== '/login' && path !== '/register' && path !== '/') {
        localStorage.removeItem('ingres_token');
        localStorage.removeItem('ingres_user');
        window.location.href = '/login?expired=true';
      }
    }

    return Promise.reject(error);
  }
);

export default api;