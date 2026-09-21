import { createApiClient, type TokenPair } from '@traveo/shared';
import { API_URL } from '@/config';
import { storage } from '@traveo/mobile-ui';

const TOKEN_KEY = 'traveo.driver.tokens';
let cache: TokenPair | null | undefined;
let onUnauthorized: (() => void) | null = null;

export const tokenStore = {
  async get(): Promise<TokenPair | null> {
    if (cache !== undefined && cache !== null) return cache;
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
