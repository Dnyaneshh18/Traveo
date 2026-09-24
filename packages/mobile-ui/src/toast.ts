import { create } from 'zustand';
import type { ConnectionState } from '@traveo/shared';

export interface Toast {
  id: number;
  key?: string;
  title: string;
  body?: string;
  kind: 'info' | 'success' | 'error';
  durationMs?: number;
  action?: {
    label: string;
    onPress: () => void;
  };
}

interface UiState {
  connection: ConnectionState;
  toasts: Toast[];
  setConnection: (s: ConnectionState) => void;
  toast: (title: string, body?: string, kind?: Toast['kind'], action?: Toast['action'], key?: string, durationMs?: number) => void;
  dismiss: (id: number) => void;
  dismissByKey: (key: string) => void;
}

let seq = 1;

export const useUiStore = create<UiState>((set) => ({
  connection: 'idle',
  toasts: [],
  setConnection: (connection) => set({ connection }),
  toast: (title, body, kind = 'info', action, key, durationMs = 8000) => {
    const id = seq++;
    set((s) => {
      // If a toast with this unique key already exists, replace it instead of creating duplicates
      const filtered = key ? s.toasts.filter((t) => t.key !== key) : s.toasts;
      return { toasts: [...filtered.slice(-2), { id, key, title, body, kind, action, durationMs }] };
    });
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, durationMs);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  dismissByKey: (key) => set((s) => ({ toasts: s.toasts.filter((t) => t.key !== key) })),
}));

export const toast = (
  title: string,
  body?: string,
  kind?: Toast['kind'],
  action?: Toast['action'],
  key?: string,
  durationMs?: number,
) => useUiStore.getState().toast(title, body, kind, action, key, durationMs);

export const dismissToastByKey = (key: string) => useUiStore.getState().dismissByKey(key);
