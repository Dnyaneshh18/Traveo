import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Resolve the backend URL.
 *  1. EXPO_PUBLIC_API_URL (inlined at build time) / app.config extra.apiUrl
 *  2. Web: relative origin (the dev server proxies /api and /ws directly to :8000)
 *  3. Development (Native): the Metro host (LAN IP) on port 8000
 *  4. Android emulator fallback: 10.0.2.2:8000
 */
export function resolveApiUrl(): string {
  const extraUrl = (Constants.expoConfig?.extra as any)?.apiUrl;
  const fromEnv = process.env.EXPO_PUBLIC_API_URL || (typeof extraUrl === 'string' ? extraUrl : '');
  if (fromEnv && /^https?:\/\//.test(fromEnv)) return fromEnv.replace(/\/+$/, '');

  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return window.location.origin;
  }

  const hostUri = Constants.expoConfig?.hostUri || (Constants as any).manifest2?.extra?.expoGo?.debuggerHost;
  if (hostUri) {
    const host = String(hostUri).split(':')[0];
    return `http://${host}:8000`;
  }
  return 'http://10.0.2.2:8000'; // Android emulator → host machine
}

export function resolveWsBaseUrl(): string {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const host = window.location.hostname;
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If in sandbox proxy domain: e.g. 8081-xxxx.e2b.app -> 8000-xxxx.e2b.app
    const m = host.match(/^(\d+)-(.+)$/);
    if (m) {
      return `${proto}//8000-${m[2]}`;
    }
    // Local dev: connect directly to backend port 8000
    return `${proto}//${host}:8000`;
  }
  const apiUrl = resolveApiUrl();
  return apiUrl.replace(/^http/, 'ws');
}

export const API_URL = resolveApiUrl();
export const APP_NAME = 'Traveo';
export const LOCATION_PUSH_INTERVAL_MS = 4000;
