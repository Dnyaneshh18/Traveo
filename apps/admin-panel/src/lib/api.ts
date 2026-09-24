import { createApiClient, RealtimeClient, type TokenPair } from '@traveo/shared';

const KEY = 'traveo.admin.tokens';
let cache: TokenPair | null | undefined;

export const tokenStore = {
  get(): TokenPair | null {
    if (cache !== undefined) return cache;
    const raw = localStorage.getItem(KEY);
    cache = raw ? (JSON.parse(raw) as TokenPair) : null;
    return cache;
  },
  set(t: TokenPair | null) {
    cache = t;
    if (t) localStorage.setItem(KEY, JSON.stringify(t));
    else localStorage.removeItem(KEY);
  },
};

const listeners = new Set<() => void>();
export const onUnauthorized = (fn: () => void) => {
  listeners.add(fn);
  return () => listeners.delete(fn);
};

// Same-origin: Vite dev server / production reverse-proxy forwards /api and /ws to the backend.
export const api = createApiClient({
  baseUrl: import.meta.env.VITE_API_URL || window.location.origin,
  tokens: tokenStore,
  onUnauthorized: () => listeners.forEach((l) => l()),
});

export const realtime = new RealtimeClient({
  url: () => {
    const t = tokenStore.get();
    return t ? api.wsUrl(t.access_token) : null;
  },
});
