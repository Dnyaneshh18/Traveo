/**
 * Incoming ride offer — full-screen modal with a 20s countdown ring (Uber/Ola style).
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Animated, Modal, StyleSheet, Text, View } from 'react-native';
import { useMutation } from '@tanstack/react-query';
import { ApiError, colors, decodePolyline, formatINR, formatKm, formatMinutes, radii, shadows, spacing, VEHICLE_BY_TYPE, type LatLng } from '@traveo/shared';
import { Body, BodyBold, Button, Caption, H1, H3, MapView, Row, Small, toast, type MapMarker } from '@traveo/mobile-ui';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useDriver } from '@/store/driver';
import { TRIP_KEY } from '@/hooks/useDriverRuntime';

export function OfferModal({ onAccepted }: { onAccepted: () => void }) {
  const offer = useDriver((s) => s.offer);
  const setOffer = useDriver((s) => s.setOffer);
  const fix = useDriver((s) => s.fix);
  const [remaining, setRemaining] = useState(0);
  const progress = useMemo(() => new Animated.Value(1), [offer?.offer_id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!offer) return;
    const end = new Date(offer.expires_at).getTime();
    const total = Math.max(1, offer.timeout_seconds);
    const tick = () => {
      const left = Math.max(0, Math.ceil((end - Date.now()) / 1000));
      setRemaining(left);
      progress.setValue(left / total);
      if (left <= 0) setOffer(null);
    };
    tick();
    const t = setInterval(tick, 250);
    return () => clearInterval(t);
  }, [offer, progress, setOffer]);

  const accept = useMutation({
    mutationFn: () => api.drivers.accept(offer!.offer_id),
    onSuccess: (res) => {
      queryClient.setQueryData(TRIP_KEY, res.data);
      setOffer(null);
      toast('Ride accepted ✅', 'Head to the first pickup.', 'success');
      onAccepted();
    },
    onError: (e) => {
      toast('Offer no longer available', e instanceof ApiError ? e.message : undefined, 'error');
      setOffer(null);
    },
  });
  const reject = useMutation({
    mutationFn: () => api.drivers.reject(offer!.offer_id, 'declined'),
    onSettled: () => setOffer(null),
  });

  if (!offer) return null;
  const polyline = offer.polyline ? decodePolyline(offer.polyline) : undefined;
  const markers: MapMarker[] = [
    { id: 'pickup', lat: offer.pickup_lat, lng: offer.pickup_lng, kind: 'pickup', label: '1' },
    { id: 'drop', lat: offer.destination_lat, lng: offer.destination_lng, kind: 'drop' },
  ];
  if (fix) markers.push({ id: 'me', lat: fix.lat, lng: fix.lng, kind: 'driver', heading: fix.heading ?? 0 });
  const fitTo: LatLng[] = [...(polyline ?? [markers[0], markers[1]]), ...(fix ? [{ lat: fix.lat, lng: fix.lng }] : [])];
  const v = VEHICLE_BY_TYPE[offer.vehicle_type];

  return (
    <View style={styles.webOverlay}>
      <View style={styles.modalCard}>
        <View style={{ height: 180, position: 'relative' }}>
          <MapView markers={markers} polyline={polyline} fitTo={fitTo} interactive={false} />
          <View style={styles.timer}>
            <Text style={styles.timerTxt}>{remaining}</Text>
            <Caption>sec</Caption>
          </View>
        </View>
        <View style={styles.bar}><Animated.View style={[styles.barFill, { width: progress.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }) }]} /></View>
        <View style={{ padding: spacing.lg, gap: spacing.md }}>
          <Row between>
            <View>
              <Caption>New student ride · {v.label}</Caption>
              <H1>{formatINR(offer.driver_payout_inr)}</H1>
              <Small>{offer.passenger_count} student{offer.passenger_count === 1 ? '' : 's'} · {offer.stops} stops · fare {formatINR(offer.fare_total_inr)}</Small>
            </View>
            <Text style={{ fontSize: 44 }}>{v.emoji}</Text>
          </Row>
          <View style={styles.route}>
            <Row gap={10}>
              <View style={[styles.dot, { backgroundColor: colors.pickup }]} />
              <View style={{ flex: 1 }}>
                <Caption>Pickup · {formatKm(offer.distance_to_pickup_km)} · ~{formatMinutes(offer.eta_to_pickup_min)} away</Caption>
                <BodyBold numberOfLines={2}>{offer.pickup_address}</BodyBold>
              </View>
            </Row>
            <View style={styles.vline} />
            <Row gap={10}>
              <View style={[styles.dot, { backgroundColor: colors.drop }]} />
              <View style={{ flex: 1 }}>
                <Caption>Drop · {formatKm(offer.route_distance_km)} · {formatMinutes(offer.route_duration_min)}</Caption>
                <BodyBold numberOfLines={2}>{offer.destination_address}</BodyBold>
              </View>
            </Row>
          </View>
          {offer.note ? <Body>“{offer.note}”</Body> : null}
          <Row gap={spacing.md} style={{ marginTop: spacing.sm }}>
            <Button title="Decline" variant="ghost" onPress={() => reject.mutate()} style={{ flex: 1 }} />
            <Button title={`Accept · ${remaining}s`} variant="primary" onPress={() => accept.mutate()} loading={accept.isPending} style={{ flex: 2, backgroundColor: colors.success }} />
          </Row>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  webOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 999999,
    elevation: 999999,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.md,
  },
  modalCard: {
    width: '100%',
    maxWidth: 440,
    backgroundColor: colors.background,
    borderRadius: radii.xl,
    overflow: 'hidden',
    zIndex: 1000000,
    elevation: 1000000,
  },
  timer: { position: 'absolute', top: 16, right: 16, width: 56, height: 56, borderRadius: 28, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: colors.success, ...shadows.float },
  timerTxt: { fontSize: 20, fontWeight: '800', color: colors.text, lineHeight: 22 },
  bar: { height: 6, backgroundColor: colors.surfaceAlt },
  barFill: { height: 6, backgroundColor: colors.success },
  route: { backgroundColor: colors.surface, borderRadius: radii.lg, padding: spacing.md, gap: 4, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  dot: { width: 10, height: 10, borderRadius: 5 },
  vline: { width: 2, height: 16, backgroundColor: colors.border, marginLeft: 4 },
});
