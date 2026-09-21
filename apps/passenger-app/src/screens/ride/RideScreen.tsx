import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useMutation } from '@tanstack/react-query';
import {
  ApiError,
  colors,
  decodePolyline,
  departureLabel,
  formatINR,
  formatMinutes,
  radii,
  shadows,
  spacing,
  STATUS_LABEL,
  type LatLng,
  type RideRequest,
} from '@traveo/shared';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { realtime } from '@/lib/realtime';
import { useAuth } from '@/store/auth';
import { useLive } from '@/store/live';
import { useRideDetail } from '@/hooks/useActiveRide';
import { CodeCard, DispatchRadar, FareSummary, MemberRow } from '@/components/ride';
import type { AppStackParamList } from '@/navigation/types';
import { watchPosition, toast, MapView, type MapMarker, Avatar, Body, BodyBold, Button, Caption, Card, H2, H3, Loading, Pill, Row, Screen, Small, SmallBold, Spacer } from '@traveo/mobile-ui';

type Props = NativeStackScreenProps<AppStackParamList, 'Ride'>;

function confirm(title: string, message: string, onYes: () => void, destructive = true) {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.confirm(`${title}\n\n${message}`)) onYes();
    return;
  }
  Alert.alert(title, message, [
    { text: 'Keep', style: 'cancel' },
    { text: 'Yes', style: destructive ? 'destructive' : 'default', onPress: onYes },
  ]);
}

export function RideScreen({ navigation, route }: Props) {
  const { requestId } = route.params;
  const user = useAuth((s) => s.user);
  const detail = useRideDetail(requestId);
  const req = detail.data;
  const driverPos = useLive((s) => s.driver);
  const riders = useLive((s) => s.riders);
  const dispatch = useLive((s) => s.dispatch);
  const [me, setMe] = useState<LatLng | null>(null);
  const [tab, setTab] = useState<'group' | 'fare'>('group');
  const stopWatch = useRef<() => void>(() => {});

  const isCreator = req?.my_role === 'creator';
  const isMember = !!req?.my_role && (req.my_status === 'accepted' || req.my_status === 'picked_up');
  const live = req?.status === 'driver_assigned' || req?.status === 'in_progress';

  // Subscribe to the ride topic & stream my location while the driver is coming.
  useEffect(() => {
    realtime.subscribe(`ride:${requestId}`);
    return () => {
      realtime.unsubscribe(`ride:${requestId}`);
    };
  }, [requestId]);

  useEffect(() => {
    if (!isMember || !live) return;
    let cancelled = false;
    watchPosition((fix) => {
      if (cancelled) return;
      setMe({ lat: fix.lat, lng: fix.lng });
      realtime.sendLocation(fix);
    }, 5000).then((stop) => {
      stopWatch.current = stop;
      if (cancelled) stop();
    });
    return () => {
      cancelled = true;
      stopWatch.current();
    };
  }, [isMember, live]);

  useEffect(() => {
    if (req?.status === 'completed' && isMember) navigation.replace('RideComplete', { requestId });
  }, [req?.status, isMember, navigation, requestId]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['rides'] });
    queryClient.invalidateQueries({ queryKey: ['feed'] });
  };
  const onError = (e: unknown) => toast('Something went wrong', e instanceof ApiError ? e.message : undefined, 'error');
  const lock = useMutation({ mutationFn: () => api.rides.lock(requestId), onSuccess: () => { invalidate(); toast('Finding your driver 🚕'); }, onError });
  const retry = useMutation({ mutationFn: () => api.rides.retry(requestId), onSuccess: invalidate, onError });
  const reopen = useMutation({ mutationFn: () => api.rides.reopen(requestId), onSuccess: invalidate, onError });
  const cancel = useMutation({ mutationFn: () => api.rides.cancel(requestId, 'creator_cancelled'), onSuccess: () => { invalidate(); navigation.popToTop(); }, onError });
  const leave = useMutation({ mutationFn: () => api.rides.leave(requestId), onSuccess: () => { invalidate(); navigation.popToTop(); }, onError });
  const remove = useMutation({ mutationFn: (userId: string) => api.rides.removeMember(requestId, userId), onSuccess: invalidate, onError });

  const polyline = useMemo(() => (req?.route_polyline ? decodePolyline(req.route_polyline) : undefined), [req?.route_polyline]);
  const markers = useMemo<MapMarker[]>(() => {
    if (!req) return [];
    const out: MapMarker[] = [];
    const activeMembers = req.members.filter((m) => m.status === 'accepted' || m.status === 'picked_up');
    const seen = new Set<string>();
    for (const m of activeMembers) {
      const pk = `${m.pickup_lat.toFixed(4)},${m.pickup_lng.toFixed(4)}`;
      if (!seen.has(pk)) {
        seen.add(pk);
        out.push({ id: `p-${pk}`, lat: m.pickup_lat, lng: m.pickup_lng, kind: req.direction === 'from_college' ? 'campus' : 'pickup', label: m.pickup_order ? String(m.pickup_order) : undefined });
      }
      const dk = `${m.drop_lat.toFixed(4)},${m.drop_lng.toFixed(4)}`;
      if (!seen.has(dk)) {
        seen.add(dk);
        out.push({ id: `d-${dk}`, lat: m.drop_lat, lng: m.drop_lng, kind: req.direction === 'to_college' ? 'campus' : 'drop', label: m.drop_order ? String(m.drop_order) : undefined });
      }
    }
    const dp = driverPos ?? (req.driver?.position && req.driver.position.lat != null ? (req.driver.position as any) : null);
    if (live && dp) out.push({ id: 'driver', lat: dp.lat, lng: dp.lng, kind: 'driver', heading: dp.heading ?? 0 });
    for (const r of Object.values(riders)) if (r.user_id !== user?.id) out.push({ id: `rider-${r.user_id}`, lat: r.lat, lng: r.lng, kind: 'rider' });
    if (me) out.push({ id: 'me', ...me, kind: 'me' });
    return out;
  }, [req, driverPos, riders, me, live, user?.id]);

  const fitTo = useMemo<LatLng[]>(() => {
    if (!req) return [];
    const pts: LatLng[] = polyline ?? [{ lat: req.origin_lat, lng: req.origin_lng }, { lat: req.destination_lat, lng: req.destination_lng }];
    const dp = driverPos ?? (req.driver?.position as any);
    return live && dp?.lat ? [...pts, { lat: dp.lat, lng: dp.lng }] : pts;
    // Only refit when the route or the driver first appears – not every GPS tick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [req?.route_polyline, req?.status, !!driverPos]);

  if (!req) return <Screen><Loading label="Loading ride…" /></Screen>;

  const activeMembers = req.members.filter((m) => m.status === 'accepted' || m.status === 'picked_up' || m.status === 'dropped');
  const headline = req.direction === 'from_college' ? `To ${req.destination_address.split(',')[0]}` : `To ${req.college_name}`;

  return (
    <Screen padded={false} edges={['top']}>
      <View style={{ flex: 1 }}>
        <MapView markers={markers} polyline={polyline} fitTo={fitTo} showUserLocation={live} />
        <Pressable onPress={() => navigation.canGoBack() ? navigation.goBack() : navigation.popToTop()} style={styles.back}><BodyBold>←</BodyBold></Pressable>
        <View style={styles.statusChip}><Pill label={STATUS_LABEL[req.status]} status={req.status} /></View>
        {live && req.driver ? <DriverBanner req={req} eta={driverPos ? undefined : req.driver.eta_min} /> : null}
      </View>

      <View style={styles.sheet}>
        <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md }} showsVerticalScrollIndicator={false}>
          <Row between>
            <View style={{ flex: 1 }}>
              <H2 numberOfLines={1}>{headline}</H2>
              <Small>{req.vehicle_label} · {req.seats_taken}/{req.seat_capacity} seats · {departureLabel(req.departure_at)}</Small>
            </View>
            <Text style={{ fontSize: 30 }}>{req.direction === 'from_college' ? '🏠' : '🎓'}</Text>
          </Row>

          {req.status === 'locked' ? (
            <Card>
              <DispatchRadar radiusKm={dispatch?.radius_km ?? req.dispatch?.radius_km} maxRadiusKm={req.dispatch?.max_radius_km ?? 8} attempts={dispatch?.attempts ?? req.dispatch?.attempts ?? 0} phase={dispatch?.phase} />
              {isCreator ? (
                <Row gap={spacing.sm}>
                  <Button title="Wait for more riders" variant="secondary" size="md" onPress={() => reopen.mutate()} loading={reopen.isPending} style={{ flex: 1 }} />
                  <Button title="Cancel" variant="danger" size="md" onPress={() => confirm('Cancel this ride?', 'Everyone in the group will be notified.', () => cancel.mutate())} style={{ flex: 1 }} />
                </Row>
              ) : null}
            </Card>
          ) : null}

          {req.status === 'no_driver' ? (
            <Card style={{ backgroundColor: colors.dangerLight, borderWidth: 0, gap: spacing.sm }}>
              <H3>No drivers accepted yet</H3>
              <Small>We pinged {req.dispatch?.attempts ?? 0} driver(s) up to {req.dispatch?.max_radius_km ?? 8} km away. Try again or wait for more co-riders (bigger groups get picked up faster).</Small>
              {isCreator ? (
                <Row gap={spacing.sm}>
                  <Button title="Search again" size="md" onPress={() => retry.mutate()} loading={retry.isPending} style={{ flex: 1 }} />
                  <Button title="Reopen" variant="secondary" size="md" onPress={() => reopen.mutate()} style={{ flex: 1 }} />
                </Row>
              ) : null}
            </Card>
          ) : null}

          {live && req.my_code && req.my_code_kind ? <CodeCard code={req.my_code} kind={req.my_code_kind} /> : null}
          {req.status === 'in_progress' && req.my_status === 'picked_up' ? (
            <Card style={{ backgroundColor: colors.successLight, borderWidth: 0 }}><BodyBold color="#15803D">You're on board 🚗 Sit back – your stop is {req.members.find((m) => m.is_me)?.drop_address.split(',')[0]}.</BodyBold></Card>
          ) : null}

          {req.status === 'open' ? (
            <Card style={{ backgroundColor: colors.primaryLight, borderWidth: 0, gap: spacing.sm }}>
              <Row between>
                <View style={{ flex: 1 }}>
                  <BodyBold>{req.seats_available > 0 ? `${req.seats_available} seat${req.seats_available === 1 ? '' : 's'} still open` : 'Group is full'}</BodyBold>
                  <Small>{isCreator ? "Leave whenever you're ready – no need to wait for a full vehicle." : 'The ride lead decides when to call the driver.'}</Small>
                </View>
              </Row>
              {isCreator ? <Button title={activeMembers.length > 1 ? `Find driver for ${activeMembers.length} of us` : 'Find driver now'} onPress={() => lock.mutate()} loading={lock.isPending} /> : null}
            </Card>
          ) : null}

          <Row gap={spacing.sm}>
            {(['group', 'fare'] as const).map((t) => (
              <Pressable key={t} onPress={() => setTab(t)} style={[styles.tab, tab === t && { backgroundColor: colors.text }]}>
                <SmallBold color={tab === t ? '#fff' : colors.textSecondary}>{t === 'group' ? `Group (${activeMembers.length})` : 'Fare'}</SmallBold>
              </Pressable>
            ))}
          </Row>
          {tab === 'group' ? (
            <Card style={{ paddingVertical: spacing.sm }}>
              {activeMembers.map((m) => (
                <MemberRow key={m.id} member={m} showOrder={live} canRemove={isCreator && !m.is_me && req.status === 'open' && m.status === 'accepted'} onRemove={() => confirm(`Remove ${m.full_name}?`, 'They will be notified.', () => remove.mutate(m.user_id))} />
              ))}
              {req.note ? <Small style={{ marginTop: spacing.sm }}>Note from lead: “{req.note}”</Small> : null}
            </Card>
          ) : (
            <FareSummary request={req} />
          )}

          {isMember && req.status !== 'in_progress' && req.status !== 'completed' ? (
            <View style={{ alignItems: 'center', marginTop: spacing.sm }}>
              {isCreator ? (
                req.status !== 'locked' && req.status !== 'no_driver' ? (
                  <Pressable onPress={() => confirm('Cancel this ride?', activeMembers.length > 1 ? 'Everyone in your group will be notified.' : 'You can always post a new one.', () => cancel.mutate())}>
                    <Small color={colors.danger}>Cancel ride for everyone</Small>
                  </Pressable>
                ) : null
              ) : (
                <Pressable onPress={() => confirm('Leave this ride?', 'Your seat will be freed for someone else.', () => leave.mutate())}>
                  <Small color={colors.danger}>Leave ride</Small>
                </Pressable>
              )}
            </View>
          ) : null}
          {!isMember && req.status === 'open' ? <Button title="Join this ride" onPress={() => navigation.navigate('JoinRide', { requestId })} /> : null}
        </ScrollView>
      </View>
    </Screen>
  );
}

function DriverBanner({ req, eta }: { req: RideRequest; eta?: number | null }) {
  const d = req.driver!;
  const dispatchEta = useLive((s) => s.dispatch?.eta_min);
  const shownEta = eta ?? dispatchEta ?? d.eta_min;
  return (
    <View style={styles.driverBanner}>
      <Avatar name={d.full_name} size={44} color={colors.driver} />
      <View style={{ flex: 1 }}>
        <Row gap={6}><BodyBold numberOfLines={1}>{d.full_name}</BodyBold><Small>★ {d.rating}</Small></Row>
        <Small numberOfLines={1}>{d.vehicle_label} · {d.color ? `${d.color} ` : ''}{d.make_model ?? ''}</Small>
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        <View style={styles.plate}><Text style={styles.plateTxt}>{d.registration_number}</Text></View>
        <Caption>{req.status === 'in_progress' ? 'on trip' : shownEta ? `~${formatMinutes(shownEta)} away` : 'on the way'}</Caption>
      </View>
    </View>
  );
}

export function RideCompleteScreen({ navigation, route }: NativeStackScreenProps<AppStackParamList, 'RideComplete'>) {
  const { requestId } = route.params;
  const detail = useRideDetail(requestId);
  const req = detail.data;
  const [stars, setStars] = useState(5);
  const [paid, setPaid] = useState(false);
  const rate = useMutation({
    mutationFn: () => api.rides.rate({ ride_id: req!.ride!.id, ratee_id: req!.driver!.user_id, stars }),
    onSuccess: () => toast('Thanks for rating ⭐', undefined, 'success'),
    onError: (e) => toast('Could not submit rating', e instanceof ApiError ? e.message : undefined, 'error'),
  });
  const pay = useMutation({
    mutationFn: () => api.rides.confirmPayment(req!.ride!.id, 'cash'),
    onSuccess: () => { setPaid(true); toast('Payment recorded', undefined, 'success'); },
  });
  useEffect(() => { useLive.getState().reset(); }, []);
  if (!req) return <Screen><Loading /></Screen>;
  const mine = req.members.find((m) => m.is_me);
  return (
    <Screen style={{ justifyContent: 'center' }}>
      <Card style={{ alignItems: 'center', gap: spacing.md }}>
        <Text style={{ fontSize: 52 }}>🎯</Text>
        <H2 center>You've arrived!</H2>
        <Small center>{req.origin_address.split(',')[0]} → {req.destination_address.split(',')[0]}</Small>
        <View style={{ alignItems: 'center' }}>
          <Caption>Your share</Caption>
          <Text style={{ fontSize: 40, fontWeight: '800', color: colors.primaryDark }}>{formatINR(mine?.fare_share_inr)}</Text>
          {req.my_savings_inr ? <SmallBold color="#15803D">You saved {formatINR(req.my_savings_inr)} by sharing 🎉</SmallBold> : null}
        </View>
        <Button title={paid ? 'Paid in cash ✓' : 'I paid the driver (cash/UPI)'} variant={paid ? 'secondary' : 'primary'} onPress={() => pay.mutate()} disabled={paid} loading={pay.isPending} style={{ alignSelf: 'stretch' }} />
        <Spacer h={spacing.xs} />
        <Body>Rate {req.driver?.full_name?.split(' ')[0] ?? 'your driver'}</Body>
        <Row gap={6}>
          {[1, 2, 3, 4, 5].map((s) => (
            <Pressable key={s} onPress={() => setStars(s)}><Text style={{ fontSize: 34, opacity: s <= stars ? 1 : 0.25 }}>⭐</Text></Pressable>
          ))}
        </Row>
        <Button title="Submit rating" variant="secondary" onPress={() => rate.mutate()} loading={rate.isPending} disabled={rate.isSuccess} style={{ alignSelf: 'stretch' }} />
        <Pressable onPress={() => navigation.popToTop()}><Small color={colors.primary}>Back to home</Small></Pressable>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { position: 'absolute', top: 12, left: 12, width: 40, height: 40, borderRadius: 20, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center', ...shadows.card },
  statusChip: { position: 'absolute', top: 18, right: 12 },
  sheet: { maxHeight: '58%', backgroundColor: colors.background, borderTopLeftRadius: radii.xl, borderTopRightRadius: radii.xl, marginTop: -20, ...shadows.float },
  tab: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: radii.pill, backgroundColor: colors.surfaceAlt },
  driverBanner: { position: 'absolute', left: 12, right: 12, bottom: 32, backgroundColor: colors.surface, borderRadius: radii.lg, padding: 12, flexDirection: 'row', alignItems: 'center', gap: 12, ...shadows.float },
  plate: { backgroundColor: '#FDE68A', borderWidth: 1.5, borderColor: '#111827', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 2 },
  plateTxt: { fontWeight: '800', letterSpacing: 1, color: '#111827', fontSize: 13 },
});
