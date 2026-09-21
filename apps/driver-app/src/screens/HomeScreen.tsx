import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ApiError, colors, formatINR, radii, shadows, spacing, type LatLng } from '@traveo/shared';
import { Avatar, BodyBold, Caption, Card, ConnectionDot, ensureLocationPermission, getCurrentFix, H2, H3, MapView, Pill, Row, Small, SmallBold, toast, type MapMarker } from '@traveo/mobile-ui';
import { api } from '@/lib/api';
import { useAuth } from '@/store/auth';
import { useDriver } from '@/store/driver';
import { useTrip } from '@/hooks/useDriverRuntime';
import type { AppStackParamList } from '@/navigation/types';

import { OfferModal } from '@/screens/OfferModal';
import { RatingModal, type PendingRatingData } from '@/screens/RatingModal';

export function HomeScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const user = useAuth((s) => s.user);
  const refreshUser = useAuth((s) => s.refreshUser);
  const online = useDriver((s) => s.online);
  const setOnline = useDriver((s) => s.setOnline);
  const fix = useDriver((s) => s.fix);
  const setFix = useDriver((s) => s.setFix);
  const { data: trip } = useTrip();
  const [ratingDismissed, setRatingDismissed] = useState(false);
  const earnings = useQuery({ queryKey: ['driver', 'earnings'], queryFn: async () => (await api.drivers.earnings()).data, refetchInterval: 30000 });
  const pendingRating = useQuery({
    queryKey: ['ratings', 'pending'],
    queryFn: async () => (await api.rides.pendingRating()).data,
    refetchInterval: 15000,
  });
  const [busy, setBusy] = useState(false);

  // Restore online state from the server profile.
  useEffect(() => {
    const s = user?.driver?.status;
    if (s === 'online' || s === 'on_trip') setOnline(true);
  }, [user?.driver?.status, setOnline]);

  useEffect(() => {
    getCurrentFix().then((f) => f && setFix(f));
  }, [setFix]);

  useEffect(() => {
    if (trip && (trip.ride.status === 'driver_assigned' || trip.ride.status === 'in_progress')) navigation.navigate('Trip');
  }, [trip?.ride.id, trip?.ride.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = useMutation({
    mutationFn: async (next: boolean) => {
      if (next) {
        const ok = await ensureLocationPermission();
        const f = (await getCurrentFix()) ?? fix ?? { lat: 18.4638, lng: 73.8680 };
        return (await api.drivers.setStatus(true, f?.lat, f?.lng)).data;
      }
      return (await api.drivers.setStatus(false)).data;
    },
    onMutate: () => setBusy(true),
    onSuccess: (data, next) => {
      setOnline(next);
      toast(next ? "You're online 🟢" : "You're offline", next ? 'Waiting for ride requests near you.' : undefined, next ? 'success' : 'info');
      refreshUser();
      void data;
    },
    onError: (e) => toast('Could not change status', e instanceof ApiError ? e.message : undefined, 'error'),
    onSettled: () => setBusy(false),
  });

  const center: LatLng | undefined = fix ? { lat: fix.lat, lng: fix.lng } : undefined;
  const markers = useMemo<MapMarker[]>(() => (fix ? [{ id: 'me', lat: fix.lat, lng: fix.lng, kind: 'driver', heading: fix.heading ?? 0 }] : []), [fix]);
  const fitTo = useMemo<LatLng[]>(() => (center ? [center] : []), [center?.lat ? Math.round(center.lat * 100) : 0]); // eslint-disable-line react-hooks/exhaustive-deps
  const vehicle = user?.driver?.vehicle;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={{ flex: 1 }}>
        <MapView center={center} zoom={14} markers={markers} fitTo={fitTo} showUserLocation followUser={online} />
        <View style={styles.topBar} pointerEvents="box-none">
          <Card style={styles.headerCard}>
            <Row between>
              <Row gap={10}>
                <Avatar name={user?.full_name || 'D'} size={38} color={colors.driver} />
                <View>
                  <BodyBold numberOfLines={1}>{user?.full_name}</BodyBold>
                  <Small>{vehicle?.registration_number} · ★ {user?.driver?.average_rating.toFixed(1)}</Small>
                </View>
              </Row>
              <Row gap={10}>
                <ConnectionDot />
                <Pill label={online ? 'online' : 'offline'} status={online ? 'online' : 'offline'} />
              </Row>
            </Row>
          </Card>
        </View>
      </View>

      <View style={styles.sheet}>
        <Row between>
          <View>
            <H2>{online ? 'Looking for rides…' : "You're offline"}</H2>
            <Small>{online ? 'Stay in the app – requests arrive with a 20s countdown.' : 'Go online to receive student group rides.'}</Small>
          </View>
          <Switch value={online} onValueChange={(v) => toggle.mutate(v)} disabled={busy} trackColor={{ true: colors.success }} thumbColor="#fff" style={{ transform: [{ scale: 1.2 }] }} />
        </Row>
        <Row gap={spacing.md} style={{ marginTop: spacing.lg }}>
          <Stat label="Today" value={formatINR(earnings.data?.today_earnings_inr ?? 0)} sub={`${earnings.data?.today_rides ?? 0} rides`} />
          <Stat label="Total" value={formatINR(earnings.data?.total_earnings_inr ?? user?.driver?.total_earnings_inr ?? 0, { compact: true })} sub={`${earnings.data?.total_rides ?? user?.driver?.completed_rides ?? 0} rides`} />
          <Stat label="Acceptance" value={`${Math.round((earnings.data?.acceptance_rate ?? user?.driver?.acceptance_rate ?? 1) * 100)}%`} sub="keep it high" />
        </Row>
        <Row gap={spacing.md} style={{ marginTop: spacing.md }}>
          <Pressable style={styles.link} onPress={() => navigation.navigate('History')}><SmallBold color={colors.driver}>Trip history →</SmallBold></Pressable>
          <Pressable style={styles.link} onPress={() => navigation.navigate('Profile')}><SmallBold color={colors.driver}>Profile →</SmallBold></Pressable>
        </Row>
        {trip ? (
          <Pressable onPress={() => navigation.navigate('Trip')} style={{ marginTop: spacing.md }}>
            <Card style={{ backgroundColor: colors.driver, borderWidth: 0 }}>
              <Row between>
                <View><Caption color="#E0F2FE">Active trip</Caption><H3 color="#fff">{trip.stops.length} stop(s) remaining</H3></View>
                <Text style={{ fontSize: 28 }}>→</Text>
              </Row>
            </Card>
          </Pressable>
        ) : null}
      </View>
      <OfferModal onAccepted={() => navigation.navigate('Trip')} />
      <RatingModal
        data={pendingRating.data as PendingRatingData | null}
        visible={!!pendingRating.data && !ratingDismissed}
        onClose={() => setRatingDismissed(true)}
      />
    </View>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <View style={styles.stat}>
      <Caption>{label}</Caption>
      <BodyBold>{value}</BodyBold>
      <Small color={colors.textMuted}>{sub}</Small>
    </View>
  );
}

const styles = StyleSheet.create({
  topBar: { position: 'absolute', top: 48, left: spacing.lg, right: spacing.lg },
  headerCard: { paddingVertical: 10, paddingHorizontal: 12, ...shadows.float },
  sheet: { backgroundColor: colors.background, borderTopLeftRadius: radii.xl, borderTopRightRadius: radii.xl, padding: spacing.lg, paddingBottom: spacing.xxl, marginTop: -24, ...shadows.float },
  stat: { flex: 1, backgroundColor: colors.surface, borderRadius: radii.md, padding: 12, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  link: { paddingVertical: 6 },
});
