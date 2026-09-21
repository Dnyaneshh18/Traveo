/**
 * Driver runtime: GPS streaming while online, realtime offer/ride events → store + React Query.
 */
import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { WS_EVENTS, type DriverOffer, type TripView } from '@traveo/shared';
import { toast, watchPosition } from '@traveo/mobile-ui';
import { api } from '@/lib/api';
import { realtime } from '@/lib/realtime';
import { queryClient } from '@/lib/queryClient';
import { useDriver } from '@/store/driver';
import { LOCATION_PUSH_INTERVAL_MS } from '@/config';

export const TRIP_KEY = ['driver', 'trip'];

export function useTrip() {
  return useQuery<TripView | null>({
    queryKey: TRIP_KEY,
    queryFn: async () => (await api.drivers.trip()).data,
    refetchInterval: (q) => (q.state.data ? 10000 : 30000),
  });
}

export function useDriverRuntime(enabled: boolean) {
  const online = useDriver((s) => s.online);
  const stopRef = useRef<() => void>(() => {});
  const lastRest = useRef(0);

  // Realtime bindings
  useEffect(() => {
    if (!enabled) return;
    const offs = [
      realtime.on(WS_EVENTS.offer, (p: DriverOffer) => {
        useDriver.getState().setOffer(p);
        toast('New ride request 🚕', `${p.passenger_count} student(s) · ₹${Math.round(p.driver_payout_inr ?? 0)}`, 'success');
      }),
      realtime.on(WS_EVENTS.offerExpired, (p) => {
        const cur = useDriver.getState().offer;
        if (cur && cur.offer_id === p.offer_id) useDriver.getState().setOffer(null);
      }),
      realtime.on(WS_EVENTS.riderLocation, (p) => useDriver.getState().setRider(p)),
      realtime.on(WS_EVENTS.cancelled, () => {
        toast('Ride cancelled by passengers', undefined, 'error');
        useDriver.getState().clearRiders();
        queryClient.invalidateQueries({ queryKey: TRIP_KEY });
      }),
      realtime.on(WS_EVENTS.profileUpdated, () => queryClient.invalidateQueries({ queryKey: ['me'] })),
      realtime.onAny((_p, msg) => {
        if (msg.type.startsWith('ride.') || msg.type.startsWith('group.')) queryClient.invalidateQueries({ queryKey: TRIP_KEY });
      }),
    ];
    // Recover a pending offer after reconnect / app restart.
    api.drivers.offer().then((r) => r.data && useDriver.getState().setOffer(r.data)).catch(() => {});

    // Polling fallback every 1.5s so web clients never miss an offer even if WS reconnects
    const pollInterval = setInterval(() => {
      api.drivers.offer().then((r) => {
        if (r.data) {
          const offerData = r.data;
          const prev = useDriver.getState().offer;
          if (!prev || prev.offer_id !== offerData.offer_id) {
            useDriver.getState().setOffer(offerData);
            // Single de-duplicated toast per offer_id with 10-second lifetime
            toast(
              'New ride request 🚕',
              `${offerData.passenger_count} student(s) · ₹${Math.round(offerData.driver_payout_inr ?? 0)} · ${offerData.pickup_address}`,
              'success',
              {
                label: 'ACCEPT RIDE NOW',
                onPress: () => {
                  api.drivers.accept(offerData.offer_id).then((res) => {
                    queryClient.setQueryData(TRIP_KEY, res.data);
                    useDriver.getState().setOffer(null);
                    toast('Ride accepted ✅', 'Head to the first pickup.', 'success');
                  }).catch((e) => {
                    toast('Could not accept', e?.message || 'Offer expired', 'error');
                    useDriver.getState().setOffer(null);
                  });
                },
              },
              `offer-${offerData.offer_id}`,
              10000 // 10 seconds display time
            );
          }
        } else {
          // If server reports no active offer, clear expired modal
          const prev = useDriver.getState().offer;
          if (prev) {
            useDriver.getState().setOffer(null);
          }
        }
      }).catch(() => {});
    }, 1500);

    return () => {
      clearInterval(pollInterval);
      offs.forEach((o) => o());
    };
  }, [enabled]);

  // GPS streaming while online
  useEffect(() => {
    if (!enabled || !online) {
      stopRef.current();
      return;
    }
    let cancelled = false;
    watchPosition((fix) => {
      if (cancelled) return;
      useDriver.getState().setFix(fix);
      const sent = realtime.sendLocation(fix);
      const now = Date.now();
      // REST fallback every ~10s when the socket is down (dispatch needs fresh GPS in the DB).
      if (!sent && now - lastRest.current > 10000) {
        lastRest.current = now;
        api.drivers.location(fix).catch(() => {});
      } else if (now - lastRest.current > 30000) {
        lastRest.current = now;
        api.drivers.location(fix).catch(() => {});
      }
    }, LOCATION_PUSH_INTERVAL_MS).then((stop) => {
      stopRef.current = stop;
      if (cancelled) stop();
    });
    return () => {
      cancelled = true;
      stopRef.current();
    };
  }, [enabled, online]);
}
