import { create } from 'zustand';
import type { AuthResult, User } from '@traveo/shared';
import { api, tokenStore, setUnauthorizedHandler } from '@/lib/api';
import { realtime } from '@/lib/realtime';
import { queryClient } from '@/lib/queryClient';

interface AuthState {
  status: 'loading' | 'signed_out' | 'signed_in';
  user: User | null;
  hydrate: () => Promise<void>;
  completeLogin: (result: AuthResult) => Promise<void>;
  refreshUser: () => Promise<User | null>;
  setUser: (user: User) => void;
  signOut: () => Promise<void>;
}

export const useAuth = create<AuthState>((set, get) => ({
  status: 'loading',
  user: null,
  hydrate: async () => {
    const tokens = await tokenStore.get();
    if (!tokens) return set({ status: 'signed_out', user: null });
    try {
      const me = await api.auth.me();
      set({ status: 'signed_in', user: me.data });
      realtime.connect();
    } catch {
      const still = await tokenStore.get();
      set({ status: still ? 'signed_in' : 'signed_out', user: null });
      if (still) realtime.connect();
    }
  },
  completeLogin: async (result) => {
    await tokenStore.set(result.tokens);
    set({ status: 'signed_in', user: result.user });
    realtime.reset();
  },
  refreshUser: async () => {
    try {
      const me = await api.auth.me();
      set({ user: me.data });
      return me.data;
    } catch {
      return get().user;
    }
  },
  setUser: (user) => set({ user }),
  signOut: async () => {
    const tokens = await tokenStore.get();
    try {
      await api.auth.logout(tokens?.refresh_token);
    } catch {
      /* ignore */
    }
    await tokenStore.set(null);
    realtime.disconnect();
    queryClient.clear();
    set({ status: 'signed_out', user: null });
  },
}));

setUnauthorizedHandler(() => {
  realtime.disconnect();
  queryClient.clear();
  useAuth.setState({ status: 'signed_out', user: null });
});
