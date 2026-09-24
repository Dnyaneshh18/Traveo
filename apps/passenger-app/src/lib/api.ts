import { createApiClient, type TokenPair } from '@traveo/shared';
import { API_URL } from '@/config';
import { storage } from '@traveo/mobile-ui';

const TOKEN_KEY = 'traveo.passenger.tokens';
let cache: TokenPair | null | undefined;
let onUnauthorized: (() => void) | null = null;

export const tokenStore = {
  async get(): Promise<TokenPair | null> {
    if (cache !== undefined && cache !== null) return cache;
    // On web, direct localStorage read avoids any async storage initialization lag
    if (typeof localStorage !== 'undefined') {
      try {
        const item = localStorage.getItem(TOKEN_KEY);
        if (item) {
          cache = JSON.parse(item) as TokenPair;
          return cache;
        }
      } catch {
        /* ignore */
      }
    }
    const raw = await storage.get(TOKEN_KEY);
    if (!raw) {
      cache = null;
      return null;
    }
    try {
      cache = JSON.parse(raw) as TokenPair;
    } catch {
      cache = null;
    }
    return cache;
  },
  async set(tokens: TokenPair | null) {
    cache = tokens;
    if (typeof localStorage !== 'undefined') {
      try {
        if (tokens) {
          localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
          if (typeof document !== 'undefined') {
            document.cookie = `traveo_token=${encodeURIComponent(tokens.access_token)}; path=/; max-age=2592000; SameSite=Lax`;
          }
        } else {
          localStorage.removeItem(TOKEN_KEY);
          if (typeof document !== 'undefined') {
            document.cookie = 'traveo_token=; path=/; max-age=0; SameSite=Lax';
          }
        }
      } catch {
        /* ignore */
      }
    }
    try {
      await storage.set(TOKEN_KEY, tokens ? JSON.stringify(tokens) : null);
    } catch (e) {
      console.warn('Failed to save tokens to storage:', e);
    }
  },
  peek(): TokenPair | null {
    if (cache !== undefined) return cache;
    if (typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem(TOKEN_KEY);
        return raw ? (JSON.parse(raw) as TokenPair) : null;
      } catch {
        return null;
      }
    }
    return null;
  },
};

export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export const api = createApiClient({
  baseUrl: API_URL,
  tokens: tokenStore,
  onUnauthorized: () => onUnauthorized?.(),
});
