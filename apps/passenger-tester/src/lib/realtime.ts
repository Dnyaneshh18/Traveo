import { RealtimeClient, type ConnectionState } from '@traveo/shared';
import { tokenStore } from '@/lib/api';
import { resolveWsBaseUrl } from '@/config';
import { useUiStore } from '@traveo/mobile-ui';

export const realtime = new RealtimeClient({
  url: () => {
    const t = tokenStore.peek();
    if (!t?.access_token) return null;
    const wsBase = resolveWsBaseUrl();
    return `${wsBase}/ws?token=${encodeURIComponent(t.access_token)}`;
  },
  onStateChange: (state: ConnectionState) => useUiStore.getState().setConnection(state),
});
