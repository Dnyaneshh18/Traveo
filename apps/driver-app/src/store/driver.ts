/** Driver runtime state: online flag, last GPS fix, current offer, rider live positions. */
import { create } from 'zustand';
import type { DriverOffer, LivePosition } from '@traveo/shared';

interface DriverState {
  online: boolean;
  fix: { lat: number; lng: number; heading?: number | null; speed?: number | null } | null;
  offer: DriverOffer | null;
  riders: Record<string, LivePosition>;
  setOnline: (v: boolean) => void;
  setFix: (f: DriverState['fix']) => void;
  setOffer: (o: DriverOffer | null) => void;
  setRider: (p: LivePosition) => void;
  clearRiders: () => void;
}

export const useDriver = create<DriverState>((set) => ({
  online: false,
  fix: null,
  offer: null,
  riders: {},
  setOnline: (online) => set({ online }),
  setFix: (fix) => set({ fix }),
  setOffer: (offer) => set({ offer }),
  setRider: (p) => set((s) => ({ riders: { ...s.riders, [p.user_id]: p } })),
  clearRiders: () => set({ riders: {} }),
}));
