import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RIDE_REFRESH_EVENTS, WS_EVENTS, type RideRequest } from '@traveo/shared';
import { api } from '@/lib/api';
import { realtime } from '@/lib/realtime';
import { queryClient } from '@/lib/queryClient';
import { useLive } from '@/store/live';
import { toast } from '@traveo/mobile-ui';

export const ACTIVE_KEY = ['rides', 'active'];

export function useActiveRide() {
  return useQuery<RideRequest | null>({
    queryKey: ACTIVE_KEY,
    queryFn: async () => (await api.rides.active()).data,
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      // Poll as a safety net while realtime is the primary channel.
      return s === 'locked' ? 4000 : s === 'driver_assigned' || s === 'in_progress' ? 8000 : 20000;
    },
  });
}

export function useRideDetail(requestId: string | undefined) {
  return useQuery<RideRequest>({
    queryKey: ['rides', 'detail', requestId],
    queryFn: async () => (await api.rides.detail(requestId!)).data,
    enabled: !!requestId,
  });
}

/**
 * Mount once (App level): wires realtime events into React Query + the live store,
 * and surfaces user-facing toasts for the key moments.
 */
export function useRealtimeBindings(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    const live = useLive.getState();
    const offs = [
      realtime.on(WS_EVENTS.driverLocation, (p) => useLive.getState().setDriver(p)),
      realtime.on(WS_EVENTS.riderLocation, (p) => useLive.getState().setRider(p)),
      realtime.on(WS_EVENTS.dispatchStatus, (p) => useLive.getState().setDispatch({ phase: p.phase, radius_km: p.radius_km, attempts: p.attempts, eta_min: p.eta_min })),
      realtime.on(WS_EVENTS.driverAssigned, (p) => {
        useLive.getState().setDispatch(null);
        toast('Driver assigned 🚕', p.eta_min ? `Arriving in about ${Math.round(p.eta_min)} min` : undefined, 'success');
      }),
      realtime.on(WS_EVENTS.memberJoined, (p) => toast('New co-rider', `${p.full_name || 'A classmate'} joined your ride`, 'success')),
      realtime.on(WS_EVENTS.driverArrived, () => toast('Your driver has arrived 📍', 'Share your code to board')),
      realtime.on(WS_EVENTS.completed, () => {
        useLive.getState().reset();
        toast('Ride completed 🎯', 'Thanks for riding together', 'success');
      }),
      realtime.on(WS_EVENTS.cancelled, () => {
        useLive.getState().reset();
        toast('Ride cancelled', undefined, 'error');
      }),
      realtime.on(WS_EVENTS.driverCancelled, () => toast('Driver cancelled', 'Finding you another driver…', 'error')),
      realtime.on(WS_EVENTS.noDriver, () => toast('No drivers nearby', 'Tap retry or wait for more co-riders', 'error')),
      realtime.on(WS_EVENTS.removed, () => toast('Removed from ride', undefined, 'error')),
      realtime.on(WS_EVENTS.notification, (p) => {
        if (p?.title && !String(p.title).includes('joined')) toast(p.title, p.body);
      }),
      realtime.on(WS_EVENTS.profileUpdated, () => queryClient.invalidateQueries({ queryKey: ['me'] })),
      realtime.onAny((_p, msg) => {
        if (RIDE_REFRESH_EVENTS.includes(msg.type)) {
          queryClient.invalidateQueries({ queryKey: ['rides'] });
        }
        if (msg.type.startsWith('feed.')) {
          queryClient.invalidateQueries({ queryKey: ['feed'] });
        }
      }),
    ];
    return () => {
      offs.forEach((off) => off());
      live.reset();
    };
  }, [enabled]);
}
