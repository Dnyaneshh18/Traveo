import { create } from 'zustand';
import type { ConnectionState, User } from '@traveo/shared';
import { api, onUnauthorized, realtime, tokenStore } from './api';

interface State {
  status: 'loading' | 'out' | 'in';
  user: User | null;
  connection: ConnectionState;
  toast: string | null;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  notify: (msg: string) => void;
}

export const useStore = create<State>((set) => ({
  status: 'loading',
  user: null,
  connection: 'idle',
  toast: null,
  hydrate: async () => {
    if (!tokenStore.get()) return set({ status: 'out' });
    try {
      const me = await api.auth.me();
      if (me.data.role !== 'admin') throw new Error('not admin');
      set({ status: 'in', user: me.data });
      realtime.connect();
    } catch {
      tokenStore.set(null);
      set({ status: 'out', user: null });
    }
  },
  login: async (email, password) => {
    const res = await api.auth.adminLogin(email, password);
    tokenStore.set(res.data.tokens);
    set({ status: 'in', user: res.data.user });
    realtime.reset();
  },
  logout: () => {
    tokenStore.set(null);
    realtime.disconnect();
    set({ status: 'out', user: null });
  },
  notify: (msg) => {
    set({ toast: msg });
    setTimeout(() => set({ toast: null }), 3000);
  },
}));

onUnauthorized(() => useStore.setState({ status: 'out', user: null }));
export function bindConnection() {
  // RealtimeClient exposes state; poll it cheaply for the sidebar indicator.
  setInterval(() => {
    const s = realtime.state;
    if (useStore.getState().connection !== s) useStore.setState({ connection: s });
  }, 1000);
}
