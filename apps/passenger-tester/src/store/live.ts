/**
 * Live positions received over the realtime channel (driver + co-riders),
 * kept outside React Query so map markers update at high frequency without refetching.
 */
import { create } from 'zustand';
import type { LivePosition } from '@traveo/shared';

interface LiveState {
  driver: LivePosition | null;
  riders: Record<string, LivePosition>;
  dispatch: { phase?: string; radius_km?: number; attempts?: number; eta_min?: number } | null;
  setDriver: (p: LivePosition | null) => void;
  setRider: (p: LivePosition) => void;
  setDispatch: (d: LiveState['dispatch']) => void;
  reset: () => void;
}

export const useLive = create<LiveState>((set) => ({
  driver: null,
  riders: {},
  dispatch: null,
  setDriver: (driver) => set({ driver }),
  setRider: (p) => set((s) => ({ riders: { ...s.riders, [p.user_id]: p } })),
  setDispatch: (dispatch) => set({ dispatch }),
  reset: () => set({ driver: null, riders: {}, dispatch: null }),
}));
