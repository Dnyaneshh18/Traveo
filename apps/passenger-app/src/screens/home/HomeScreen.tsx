import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import { colors, decodePolyline, formatINR, radii, shadows, spacing, STATUS_LABEL, type LatLng } from '@traveo/shared';
import { api } from '@/lib/api';
import { useAuth } from '@/store/auth';
import { useActiveRide } from '@/hooks/useActiveRide';
import type { AppStackParamList } from '@/navigation/types';
import { getCurrentFix, MapView, type MapMarker, Avatar, Body, BodyBold, Caption, Card, ConnectionDot, H2, H3, Pill, Row, Small, SmallBold } from '@traveo/mobile-ui';
import { RatingModal, type PendingRatingData } from '@/components/ride/RatingModal';

export function HomeScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const user = useAuth((s) => s.user);
  const college = user?.student?.college;
  const { data: active } = useActiveRide();
  const [me, setMe] = useState<LatLng | null>(null);
  const [ratingDismissed, setRatingDismissed] = useState(false);
  const feed = useQuery({
    queryKey: ['feed', 'home'],
    queryFn: async () => (await api.rides.feed({})).data,
    refetchInterval: 30000,
  });
  const stats = useQuery({ queryKey: ['me', 'stats'], queryFn: async () => (await api.students.stats()).data });
  const pendingRating = useQuery({
    queryKey: ['ratings', 'pending'],
    queryFn: async () => (await api.rides.pendingRating()).data,
    refetchInterval: 15000,
  });

  useEffect(() => {
    getCurrentFix().then((f) => f && setMe({ lat: f.lat, lng: f.lng }));
  }, []);

  const campus: LatLng | undefined = college ? { lat: college.latitude, lng: college.longitude } : undefined;
  const markers = useMemo<MapMarker[]>(() => {
    const out: MapMarker[] = [];
    if (campus) out.push({ id: 'campus', ...campus, kind: 'campus' });
    if (me) out.push({ id: 'me', ...me, kind: 'me' });
    for (const item of feed.data ?? []) {
      out.push({ id: `req-${item.request.id}`, lat: item.request.destination_lat, lng: item.request.destination_lng, kind: 'drop', label: `${item.request.seats_available}` });
    }
    return out;
  }, [campus, me, feed.data]);
  const fitTo = useMemo(() => [campus, me].filter(Boolean) as LatLng[], [campus?.lat, me?.lat]); // eslint-disable-line react-hooks/exhaustive-deps

  const greeting = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 17 ? 'Good afternoon' : 'Good evening';
  const openCount = feed.data?.length ?? 0;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={{ flex: 1 }}>
        <MapView center={campus} zoom={13} markers={markers} fitTo={fitTo} showUserLocation polyline={active?.route_polyline ? decodePolyline(active.route_polyline) : undefined} />
        <View style={styles.topBar} pointerEvents="box-none">
          <Card style={styles.headerCard}>
            <Row between>
              <Row gap={10}>
                <Avatar name={user?.full_name || 'S'} size={38} />
                <View>
                  <Small>{greeting},</Small>
                  <BodyBold numberOfLines={1}>{user?.full_name?.split(' ')[0]} · {college?.short_name || college?.name}</BodyBold>
                </View>
              </Row>
              <Row gap={10}>
                <ConnectionDot />
                <Pressable onPress={() => navigation.navigate('Notifications')} hitSlop={8}><Text style={{ fontSize: 20 }}>🔔</Text></Pressable>
              </Row>
            </Row>
          </Card>
        </View>
      </View>

      <View style={styles.sheet}>
        {active ? (
          <Pressable onPress={() => navigation.navigate('Ride', { requestId: active.id })}>
            <Card style={{ backgroundColor: colors.primary, borderWidth: 0 }}>
              <Row between>
                <View style={{ flex: 1 }}>
                  <Caption color="#C7D2FE">Your ride · {STATUS_LABEL[active.status]}</Caption>
                  <H3 color="#fff" numberOfLines={1}>{active.direction === 'from_college' ? `To ${active.destination_address.split(',')[0]}` : `From ${active.origin_address.split(',')[0]}`}</H3>
                  <Small color="#E0E7FF">{active.seats_taken}/{active.seat_capacity} seats · {active.vehicle_label}{active.driver ? ` · ${active.driver.full_name}` : ''}</Small>
                </View>
                <Text style={{ fontSize: 30 }}>→</Text>
              </Row>
            </Card>
          </Pressable>
        ) : (
          <>
            <H2>Where are you headed?</H2>
            <Row gap={spacing.md} style={{ marginTop: spacing.md }}>
              <Pressable style={[styles.bigBtn, { backgroundColor: colors.primary }]} onPress={() => navigation.navigate('CreateRide')}>
                <Text style={{ fontSize: 26 }}>➕</Text>
                <BodyBold color="#fff">Post a ride</BodyBold>
                <Small color="#C7D2FE">Classmates join you</Small>
              </Pressable>
              <Pressable style={[styles.bigBtn, { backgroundColor: colors.surface, borderWidth: 1.5, borderColor: colors.border }]} onPress={() => navigation.getParent()?.navigate('Feed' as never)}>
                <Text style={{ fontSize: 26 }}>🔎</Text>
                <BodyBold>Find a ride</BodyBold>
                <Small>{openCount ? `${openCount} open from ${college?.short_name || 'campus'}` : 'See who is leaving'}</Small>
              </Pressable>
            </Row>
          </>
        )}
        <Row gap={spacing.md} style={{ marginTop: spacing.md }}>
          <Stat label="Rides" value={String(stats.data?.completed_rides ?? user?.student?.completed_rides ?? 0)} />
          <Stat label="Saved" value={formatINR(stats.data?.total_saved_inr ?? user?.student?.total_saved_inr ?? 0)} />
          <Stat label="Rating" value={`${(stats.data?.average_rating ?? user?.student?.average_rating ?? 5).toFixed(1)}★`} />
          <Stat label="CO₂ saved" value={`${stats.data?.co2_saved_kg ?? 0} kg`} />
        </Row>
        {user?.student?.verification_status === 'verified' ? (
          <Row gap={6} style={{ marginTop: spacing.sm }}>
            <Pill label="verified student" status="verified" />
            <Body>{' '}</Body>
          </Row>
        ) : null}
      </View>
      <RatingModal
        data={pendingRating.data as PendingRatingData | null}
        visible={
          !!pendingRating.data &&
          !ratingDismissed &&
          (typeof localStorage === 'undefined' || !localStorage.getItem(`rated_ride_${(pendingRating.data as any)?.ride_id}`))
        }
        onClose={() => setRatingDismissed(true)}
      />
    </View>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.stat}>
      <SmallBold color={colors.text}>{value}</SmallBold>
      <Caption>{label}</Caption>
    </View>
  );
}

const styles = StyleSheet.create({
  topBar: { position: 'absolute', top: 48, left: spacing.lg, right: spacing.lg },
  headerCard: { paddingVertical: 10, paddingHorizontal: 12, ...shadows.float },
  sheet: { backgroundColor: colors.background, borderTopLeftRadius: radii.xl, borderTopRightRadius: radii.xl, padding: spacing.lg, paddingBottom: spacing.xl, marginTop: -24, ...shadows.float },
  bigBtn: { flex: 1, borderRadius: radii.lg, padding: spacing.lg, gap: 4, minHeight: 116 },
  stat: { flex: 1, backgroundColor: colors.surface, borderRadius: radii.md, padding: 10, alignItems: 'center', borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
});
