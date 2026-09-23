/**
 * Active trip — live map with the optimised route, next-stop card, code verification,
 * per-passenger actions (arrived / verify / no-show / drop) and completion summary.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Linking, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useMutation } from '@tanstack/react-query';
import { ApiError, colors, decodePolyline, formatINR, formatKm, formatMinutes, radii, shadows, spacing, type LatLng, type TripStop } from '@traveo/shared';
import { Avatar, Body, BodyBold, Button, Caption, Card, H2, H3, Loading, MapView, Pill, Row, Screen, Small, SmallBold, Spacer, toast, type MapMarker } from '@traveo/mobile-ui';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useDriver } from '@/store/driver';
import { TRIP_KEY, useTrip } from '@/hooks/useDriverRuntime';
import type { AppStackParamList } from '@/navigation/types';

type Props = NativeStackScreenProps<AppStackParamList, 'Trip'>;

function confirm(title: string, message: string, onYes: () => void) {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.confirm(`${title}\n\n${message}`)) onYes();
    return;
  }
  Alert.alert(title, message, [{ text: 'No', style: 'cancel' }, { text: 'Yes', style: 'destructive', onPress: onYes }]);
}

export function TripScreen({ navigation }: Props) {
  const { data: trip, isLoading } = useTrip();
  const fix = useDriver((s) => s.fix);
  const riders = useDriver((s) => s.riders);
  const [code, setCode] = useState('');
  const [showCode, setShowCode] = useState(false);
  const [summary, setSummary] = useState<typeof trip | null>(null);

  useEffect(() => {
    if (trip?.ride.status === 'completed') setSummary(trip);
  }, [trip]);

  const onError = (e: unknown) => toast('Action failed', e instanceof ApiError ? e.message : undefined, 'error');
  const onSuccess = (res: { data: any }) => queryClient.setQueryData(TRIP_KEY, res.data);
  const rideId = trip?.ride.id ?? '';
  const arrived = useMutation({ mutationFn: () => api.drivers.arrived(rideId), onSuccess: (r) => { onSuccess(r); toast('Passengers notified 📍'); }, onError });
  const verify = useMutation({
    mutationFn: (c: string) => api.drivers.verify(rideId, c),
    onSuccess: (r) => {
      onSuccess(r);
      setCode('');
      setShowCode(false);
      toast('Passenger boarded ✅', undefined, 'success');
      // If all pickups are completed, automatically open turn-by-turn navigation for destination
      if (r.data.next_stop && r.data.next_stop.kind === 'drop') {
        navigateTo(r.data.next_stop);
      }
    },
    onError: (e) => toast('Code not recognised', e instanceof ApiError ? e.message : undefined, 'error'),
  });
  const noShow = useMutation({ mutationFn: (memberId: string) => api.drivers.noShow(rideId, memberId), onSuccess, onError });
  const drop = useMutation({ mutationFn: (memberId: string) => api.drivers.drop(rideId, memberId), onSuccess: (r) => { onSuccess(r); if (r.data.ride.status === 'completed') setSummary(r.data); }, onError });
  const cancel = useMutation({ mutationFn: () => api.drivers.cancel(rideId, 'driver_cancelled'), onSuccess: () => { queryClient.setQueryData(TRIP_KEY, null); navigation.goBack(); }, onError });

  const polyline = useMemo(() => (trip?.request.route_polyline ? decodePolyline(trip.request.route_polyline) : undefined), [trip?.request.route_polyline]);
  const markers = useMemo<MapMarker[]>(() => {
    if (!trip) return [];
    const out: MapMarker[] = [];
    const seen = new Set<string>();
    for (const s of trip.stops) {
      const key = `${s.kind}-${s.lat.toFixed(4)},${s.lng.toFixed(4)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ id: key, lat: s.lat, lng: s.lng, kind: s.kind === 'pickup' ? 'pickup' : 'drop', label: String(s.kind === 'pickup' ? s.order : s.order - 100) });
    }
    for (const r of Object.values(riders)) out.push({ id: `rider-${r.user_id}`, lat: r.lat, lng: r.lng, kind: 'rider' });
    if (fix) out.push({ id: 'me', lat: fix.lat, lng: fix.lng, kind: 'driver', heading: fix.heading ?? 0 });
    return out;
  }, [trip, riders, fix]);
  const fitTo = useMemo<LatLng[]>(() => {
    if (!trip) return [];
    const pts: LatLng[] = trip.stops.map((s) => ({ lat: s.lat, lng: s.lng }));
    if (fix) pts.push({ lat: fix.lat, lng: fix.lng });
    return pts;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trip?.stops.length, trip?.ride.status]);

  if (summary) return <TripSummary trip={summary} onDone={() => { setSummary(null); queryClient.setQueryData(TRIP_KEY, null); navigation.goBack(); }} />;
  if (isLoading) return <Screen><Loading label="Loading trip…" /></Screen>;
  if (!trip) {
    return (
      <Screen style={{ justifyContent: 'center' }}>
        <Card style={{ alignItems: 'center', gap: spacing.md }}>
          <Text style={{ fontSize: 40 }}>🛣️</Text>
          <H3>No active trip</H3>
          <Button title="Back" variant="secondary" onPress={() => navigation.goBack()} />
        </Card>
      </Screen>
    );
  }

  const next = trip.next_stop;
  const req = trip.request;
  const pickupsLeft = trip.stops.filter((s) => s.kind === 'pickup');
  const dropsLeft = trip.stops.filter((s) => s.kind === 'drop');
  const navigateTo = (s: TripStop) => {
    // If the driver has an active GPS fix, specify `origin` so Google Maps doesn't default to IP geolocation
    const originParam = fix?.lat && fix?.lng ? `&origin=${fix.lat},${fix.lng}` : '';
    Linking.openURL(`https://www.google.com/maps/dir/?api=1${originParam}&destination=${s.lat},${s.lng}&travelmode=driving`).catch(() => {});
  };

  return (
    <Screen padded={false} edges={['top']}>
      <View style={{ flex: 1 }}>
        <MapView markers={markers} polyline={polyline} fitTo={fitTo} showUserLocation />
        <View style={styles.topPill}>
          <Pill label={trip.ride.status === 'in_progress' ? `${trip.passengers_on_board} on board` : 'heading to pickup'} status={trip.ride.status === 'in_progress' ? 'in_progress' : 'driver_assigned'} />
        </View>
      </View>
      <View style={styles.sheet}>
        <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md }} showsVerticalScrollIndicator={false}>
          {next ? (
            <Card style={{ borderColor: next.kind === 'pickup' ? colors.pickup : colors.drop, borderWidth: 1.5, gap: spacing.sm }}>
              <Row between>
                <Caption color={next.kind === 'pickup' ? colors.pickup : colors.drop}>
                  Next · {next.kind === 'pickup' ? `Pickup ${next.order}` : `Drop ${next.order - 100}`}
                  {next.eta_min ? ` · ~${formatMinutes(next.eta_min)}` : ''}
                </Caption>
                <Pressable onPress={() => navigateTo(next)}>
                  <Row gap={4}>
                    <SmallBold color={colors.driver}>🧭 Live Navigation ↗</SmallBold>
                  </Row>
                </Pressable>
              </Row>
              <H3>{next.address}</H3>
              <Row gap={10}>
                <Avatar name={next.full_name} size={36} color={next.role === 'creator' ? colors.primary : colors.rider} />
                <View style={{ flex: 1 }}>
                  <BodyBold>{next.full_name}{next.seats > 1 ? ` +${next.seats - 1}` : ''}</BodyBold>
                  <Small>{next.role === 'creator' ? 'Ride lead · has the 4-digit OTP' : `Co-rider · Matching ID: ${next.matching_code || 'TRV-'}`}</Small>
                </View>
                {next.phone ? <Pressable onPress={() => Linking.openURL(`tel:${next.phone}`)} style={styles.callBtn}><Text>📞</Text></Pressable> : null}
              </Row>
              {next.kind === 'pickup' ? (
                <Row gap={spacing.sm}>
                  <Button title="I've arrived" variant="secondary" size="md" onPress={() => arrived.mutate()} loading={arrived.isPending} style={{ flex: 1 }} />
                  <Button title="Enter code" size="md" onPress={() => setShowCode(true)} style={{ flex: 1, backgroundColor: colors.success }} />
                </Row>
              ) : (
                <View style={{ gap: spacing.xs }}>
                  <Button title="🧭 Start Turn-by-Turn Navigation" variant="secondary" onPress={() => navigateTo(next)} style={{ borderColor: colors.primary, borderWidth: 1 }} />
                  <Button title={`Drop ${next.full_name.split(' ')[0]} here · ${formatINR(next.fare_share_inr)}`} onPress={() => drop.mutate(next.member_id)} loading={drop.isPending} style={{ backgroundColor: colors.drop }} />
                </View>
              )}
            </Card>
          ) : null}

          {showCode ? (
            <Card style={{ gap: spacing.sm, backgroundColor: colors.successLight, borderWidth: 0 }}>
              <BodyBold>Boarding code</BodyBold>
              <Small>Ask for the 4-digit OTP (ride lead) or the TRV- matching ID (co-rider).</Small>
              <TextInput value={code} onChangeText={(t) => setCode(t.toUpperCase())} autoCapitalize="characters" autoFocus placeholder="1234 or TRV-7K2Q" placeholderTextColor={colors.textMuted} style={styles.codeInput} onSubmitEditing={() => verify.mutate(code)} />
              <Row gap={spacing.sm}>
                <Button title="Cancel" variant="ghost" size="md" onPress={() => { setShowCode(false); setCode(''); }} style={{ flex: 1 }} />
                <Button title="Verify & board" size="md" onPress={() => verify.mutate(code)} loading={verify.isPending} disabled={code.replace(/\s/g, '').length < 4} style={{ flex: 2, backgroundColor: colors.success }} />
              </Row>
            </Card>
          ) : null}

          <Row between>
            <View><H2>{req.destination_address.split(',')[0]}</H2><Small>{formatKm(req.route_distance_km)} · {formatMinutes(req.route_duration_min)} · payout {formatINR(trip.ride.driver_payout_inr ?? Math.round((req.estimated_fare_total ?? 0) * 0.92))}</Small></View>
            <Text style={{ fontSize: 28 }}>{req.direction === 'from_college' ? '🎓→🏠' : '🏠→🎓'}</Text>
          </Row>

          <H3>Stops</H3>
          <Card style={{ paddingVertical: spacing.sm }}>
            {[...pickupsLeft, ...dropsLeft].map((s, i) => (
              <Row key={`${s.member_id}-${s.kind}`} between style={{ paddingVertical: 8, borderTopWidth: i ? StyleSheet.hairlineWidth : 0, borderTopColor: colors.border }}>
                <Row gap={10} style={{ flex: 1 }}>
                  <View style={[styles.orderDot, { backgroundColor: s.kind === 'pickup' ? colors.pickup : colors.drop }]}><Text style={styles.orderTxt}>{s.kind === 'pickup' ? s.order : s.order - 100}</Text></View>
                  <View style={{ flex: 1 }}>
                    <BodyBold numberOfLines={1}>{s.kind === 'pickup' ? 'Pick up' : 'Drop'} {s.full_name}{s.seats > 1 ? ` (+${s.seats - 1})` : ''}</BodyBold>
                    <Small numberOfLines={1}>{s.address}</Small>
                  </View>
                </Row>
                {s.kind === 'pickup' ? (
                  <Pressable onPress={() => confirm(`Mark ${s.full_name} as no-show?`, 'Only after waiting at the pickup point. This affects their rating.', () => noShow.mutate(s.member_id))}>
                    <Small color={colors.danger}>No-show</Small>
                  </Pressable>
                ) : (
                  <Small>{formatINR(s.fare_share_inr)}</Small>
                )}
              </Row>
            ))}
            {!trip.stops.length ? <Body>All passengers dropped.</Body> : null}
          </Card>

          {trip.ride.status === 'driver_assigned' ? (
            <Pressable onPress={() => confirm('Cancel this trip?', 'The group will be re-matched with another driver. Frequent cancellations lower your acceptance score.', () => cancel.mutate())} style={{ alignSelf: 'center', padding: spacing.sm }}>
              <Small color={colors.danger}>Cancel trip</Small>
            </Pressable>
          ) : null}
          <Spacer h={spacing.md} />
        </ScrollView>
      </View>
    </Screen>
  );
}

function TripSummary({ trip, onDone }: { trip: NonNullable<ReturnType<typeof useTrip>['data']>; onDone: () => void }) {
  const dropped = trip.request.members.filter((m) => m.status === 'dropped');
  const [stars, setStars] = useState(5);
  const [rated, setRated] = useState(false);
  const ratePassengers = useMutation({
    mutationFn: () => api.rides.rate({ ride_id: trip.ride.id, stars }),
    onSuccess: () => {
      setRated(true);
      toast('Rating submitted! ⭐', undefined, 'success');
    },
    onError: (e) => toast('Rating failed', e instanceof ApiError ? e.message : undefined, 'error'),
  });

  return (
    <Screen style={{ justifyContent: 'center' }}>
      <Card style={{ alignItems: 'center', gap: spacing.md }}>
        <Text style={{ fontSize: 52 }}>🏁</Text>
        <H2 center>Trip completed</H2>
        <Small center>{trip.request.origin_address.split(',')[0]} → {trip.request.destination_address.split(',')[0]}</Small>
        <View style={{ alignItems: 'center' }}>
          <Caption>Your payout</Caption>
          <Text style={{ fontSize: 40, fontWeight: '800', color: colors.success }}>{formatINR(trip.ride.driver_payout_inr)}</Text>
          <Small>Fare {formatINR(trip.ride.total_fare_inr)} · {dropped.length} passenger{dropped.length === 1 ? '' : 's'} · {formatKm(trip.ride.total_distance_km)}</Small>
        </View>
        <View style={{ alignSelf: 'stretch', gap: 6 }}>
          {dropped.map((m) => (
            <Row key={m.id} between><Body>{m.full_name}</Body><BodyBold>{formatINR(m.fare_share_inr)} · cash/UPI</BodyBold></Row>
          ))}
        </View>
        <View style={{ alignSelf: 'stretch', alignItems: 'center', gap: 6, marginVertical: spacing.xs, backgroundColor: colors.surfaceAlt, padding: spacing.md, borderRadius: radii.md }}>
          <BodyBold>Rate your passengers</BodyBold>
          <Row gap={8}>
            {[1, 2, 3, 4, 5].map((s) => (
              <Pressable key={s} onPress={() => !rated && setStars(s)}>
                <Text style={{ fontSize: 28, opacity: s <= stars ? 1 : 0.25 }}>⭐</Text>
              </Pressable>
            ))}
          </Row>
          {!rated ? (
            <Button
              title="Submit passenger rating"
              variant="secondary"
              size="sm"
              onPress={() => ratePassengers.mutate()}
              loading={ratePassengers.isPending}
              style={{ marginTop: 4, width: '100%' }}
            />
          ) : (
            <SmallBold color={colors.success}>Rating recorded ✓</SmallBold>
          )}
        </View>
        <Button title="Back online" onPress={onDone} style={{ alignSelf: 'stretch', backgroundColor: colors.success }} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  topPill: { position: 'absolute', top: 16, right: 12 },
  sheet: { maxHeight: '60%', backgroundColor: colors.background, borderTopLeftRadius: radii.xl, borderTopRightRadius: radii.xl, marginTop: -20, ...shadows.float },
  callBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.successLight, alignItems: 'center', justifyContent: 'center' },
  codeInput: { backgroundColor: colors.surface, borderRadius: radii.md, borderWidth: 1.5, borderColor: colors.success, paddingHorizontal: 14, paddingVertical: 12, fontSize: 24, fontWeight: '800', letterSpacing: 4, color: colors.text, textAlign: 'center' },
  orderDot: { width: 26, height: 26, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  orderTxt: { color: '#fff', fontWeight: '800', fontSize: 12 },
});
