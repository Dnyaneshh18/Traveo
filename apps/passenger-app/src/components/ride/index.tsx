import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';
import {
  colors,
  departureLabel,
  formatINR,
  formatKm,
  formatMinutes,
  radii,
  spacing,
  STATUS_LABEL,
  typography,
  VEHICLE_BY_TYPE,
  VEHICLES,
  type FareOption,
  type MatchInfo,
  type RideMember,
  type RideRequest,
  type VehicleType,
} from '@traveo/shared';
import { Avatar, Body, BodyBold, Caption, Card, H2, H3, Pill, Row, Small, SmallBold } from '@traveo/mobile-ui';

// ── Vehicle picker ─────────────────────────────────────────────────
export function VehiclePicker({ value, onChange, options, seats }: { value: VehicleType; onChange: (v: VehicleType) => void; options?: FareOption[]; seats: number }) {
  return (
    <View style={{ gap: spacing.sm }}>
      {VEHICLES.map((v) => {
        const opt = options?.find((o) => o.vehicle_type === v.type);
        const active = value === v.type;
        const disabled = seats > v.capacity;
        return (
          <Pressable
            key={v.type}
            disabled={disabled}
            onPress={() => onChange(v.type)}
            style={[styles.vehicle, active && { borderColor: colors.primary, backgroundColor: colors.primaryLight }, disabled && { opacity: 0.45 }]}
          >
            <Text style={{ fontSize: 28 }}>{v.emoji}</Text>
            <View style={{ flex: 1 }}>
              <BodyBold>{v.label}</BodyBold>
              <Small>{v.capacity} seats · {v.description}</Small>
            </View>
            {opt ? (
              <View style={{ alignItems: 'flex-end' }}>
                <BodyBold color={colors.primaryDark}>{formatINR(opt.per_seat_if_full)}</BodyBold>
                <Caption>per seat if full</Caption>
                <Small color={colors.textMuted}>{formatINR(opt.total_estimate)} total</Small>
              </View>
            ) : null}
          </Pressable>
        );
      })}
    </View>
  );
}

// ── Feed card ──────────────────────────────────────────────────────
export function RideCard({ request, match, onPress, onAccept, onReject, compact }: { request: RideRequest; match?: MatchInfo | null; onPress?: () => void; onAccept?: () => void; onReject?: () => void; compact?: boolean }) {
  const v = VEHICLE_BY_TYPE[request.vehicle_type];
  const creator = request.members.find((m) => m.role === 'creator');
  const activeMembers = request.members.filter((m) => m.status === 'accepted' || m.status === 'picked_up');
  const perSeat = request.estimated_fare_total ? Math.round(request.estimated_fare_total / Math.max(1, request.seats_taken + 1)) : null;
  return (
    <Card onPress={onPress} style={{ gap: spacing.md }}>
      <Row between>
        <Row>
          <Text style={{ fontSize: 24 }}>{v.emoji}</Text>
          <View>
            <BodyBold>{request.direction === 'from_college' ? 'From campus' : 'To campus'}</BodyBold>
            <Small>{departureLabel(request.departure_at)}</Small>
          </View>
        </Row>
        <Pill label={STATUS_LABEL[request.status]} status={request.status} />
      </Row>

      <View style={{ gap: 6 }}>
        <Row gap={10}>
          <View style={[styles.dot, { backgroundColor: colors.pickup }]} />
          <Body numberOfLines={1} style={{ flex: 1 }}>{request.origin_address}</Body>
        </Row>
        <Row gap={10}>
          <View style={[styles.dot, { backgroundColor: colors.drop }]} />
          <Body numberOfLines={1} style={{ flex: 1 }}>{request.destination_address}</Body>
        </Row>
      </View>

      <Row between>
        <Row gap={-8}>
          {activeMembers.slice(0, 4).map((m, i) => (
            <View key={m.id} style={{ marginLeft: i ? -8 : 0 }}>
              <Avatar name={m.full_name} size={30} ring="#fff" color={m.role === 'creator' ? colors.primary : colors.rider} />
            </View>
          ))}
          <Small style={{ marginLeft: 12 }}>
            {creator?.full_name?.split(' ')[0] ?? 'Student'}{activeMembers.length > 1 ? ` +${activeMembers.length - 1}` : ''} · {request.seats_available} seat{request.seats_available === 1 ? '' : 's'} left
          </Small>
        </Row>
        <View style={{ alignItems: 'flex-end' }}>
          <BodyBold color={colors.primaryDark}>{perSeat ? `~${formatINR(perSeat)}` : formatINR(request.estimated_fare_total)}</BodyBold>
          <Caption>{perSeat ? 'your share' : 'total'}</Caption>
        </View>
      </Row>

      {match ? (
        <Row gap={6} style={{ flexWrap: 'wrap' }}>
          <Pill label={`${Math.round(match.score * 100)}% match`} bg={colors.successLight} color="#15803D" />
          {match.detour_km > 0.05 ? <Pill label={`+${formatKm(match.detour_km)} detour`} /> : <Pill label="on your route" />}
          {request.women_only ? <Pill label="women only" bg="#FCE7F3" color="#BE185D" /> : null}
          {request.note ? <Small numberOfLines={1} style={{ flex: 1 }}>“{request.note}”</Small> : null}
        </Row>
      ) : request.women_only ? <Pill label="women only" bg="#FCE7F3" color="#BE185D" /> : null}

      {!compact && (onAccept || onReject) ? (
        <Row gap={spacing.sm}>
          {onReject ? (
            <Pressable onPress={onReject} style={[styles.actionBtn, { backgroundColor: colors.surfaceAlt }]}>
              <SmallBold color={colors.textSecondary}>Not for me</SmallBold>
            </Pressable>
          ) : null}
          {onAccept ? (
            <Pressable onPress={onAccept} style={[styles.actionBtn, { backgroundColor: colors.primary, flex: 2 }]}>
              <SmallBold color="#fff">Accept & join</SmallBold>
            </Pressable>
          ) : null}
        </Row>
      ) : null}
    </Card>
  );
}

// ── Member row ─────────────────────────────────────────────────────
export function MemberRow({ member, canRemove, onRemove, showOrder }: { member: RideMember; canRemove?: boolean; onRemove?: () => void; showOrder?: boolean }) {
  const statusLabel: Record<string, string> = { accepted: 'Joined', picked_up: 'On board', dropped: 'Dropped', left: 'Left', removed: 'Removed', no_show: 'No-show' };
  return (
    <Row between style={{ paddingVertical: 8 }}>
      <Row gap={12} style={{ flex: 1 }}>
        <Avatar name={member.full_name} size={40} color={member.role === 'creator' ? colors.primary : colors.rider} />
        <View style={{ flex: 1 }}>
          <Row gap={6}>
            <BodyBold numberOfLines={1}>{member.is_me ? 'You' : member.full_name}</BodyBold>
            {member.role === 'creator' ? <Pill label="lead" bg={colors.primaryLight} color={colors.primaryDark} /> : null}
          </Row>
          <Small numberOfLines={1}>
            {showOrder && member.pickup_order ? `Stop ${member.pickup_order} · ` : ''}
            {member.pickup_address.split(',')[0]} → {member.drop_address.split(',')[0]}
          </Small>
        </View>
      </Row>
      <View style={{ alignItems: 'flex-end', gap: 4 }}>
        {member.fare_share_inr != null ? <BodyBold>{formatINR(member.fare_share_inr)}</BodyBold> : null}
        <Row gap={6}>
          <Pill label={statusLabel[member.status] ?? member.status} status={member.status === 'picked_up' ? 'in_progress' : member.status === 'accepted' ? 'open' : 'completed'} />
          {canRemove ? (
            <Pressable onPress={onRemove} hitSlop={8}>
              <Small color={colors.danger}>Remove</Small>
            </Pressable>
          ) : null}
        </Row>
      </View>
    </Row>
  );
}

// ── Code card (OTP / matching code) ────────────────────────────────
export function CodeCard({ code, kind }: { code: string; kind: 'otp' | 'matching_code' }) {
  const isOtp = kind === 'otp';
  return (
    <View style={[styles.codeCard, { backgroundColor: isOtp ? colors.primary : '#111827' }]}>
      <Caption color={isOtp ? '#C7D2FE' : '#9CA3AF'}>{isOtp ? 'Your boarding OTP' : 'Your matching ID'}</Caption>
      <Text style={[typography.mono, { color: '#fff', marginVertical: 6 }]}>{code}</Text>
      <Small color={isOtp ? '#E0E7FF' : '#D1D5DB'} center>
        {isOtp ? 'Tell the driver this OTP when you board. Only you (the ride lead) have it.' : 'Show this ID to the driver – it proves you belong to this group.'}
      </Small>
    </View>
  );
}

// ── Dispatch radar animation ───────────────────────────────────────
export function DispatchRadar({ radiusKm, maxRadiusKm, attempts, phase }: { radiusKm?: number | null; maxRadiusKm: number; attempts: number; phase?: string }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(Animated.timing(anim, { toValue: 1, duration: 1800, easing: Easing.out(Easing.quad), useNativeDriver: true }));
    loop.start();
    return () => loop.stop();
  }, [anim]);
  const rings = [0, 0.33, 0.66].map((offset) => {
    const v = Animated.modulo(Animated.add(anim, offset), 1);
    return { scale: v.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] }), opacity: v.interpolate({ inputRange: [0, 0.7, 1], outputRange: [0.5, 0.15, 0] }) };
  });
  const label = phase === 'offering' ? 'Driver is looking at your request…' : phase === 'retrying' ? 'Expanding the search again…' : 'Searching nearby drivers';
  return (
    <View style={styles.radar}>
      <View style={styles.radarRings}>
        {rings.map((r, i) => <Animated.View key={i} style={[styles.ring, { transform: [{ scale: r.scale }], opacity: r.opacity }]} />)}
        <View style={styles.radarCore}><Text style={{ fontSize: 26 }}>🚕</Text></View>
      </View>
      <H3 center>{label}</H3>
      <Small center>
        Within {radiusKm ? `${radiusKm} km` : '…'} of your pickup · up to {maxRadiusKm} km{attempts ? ` · ${attempts} driver${attempts === 1 ? '' : 's'} pinged` : ''}
      </Small>
    </View>
  );
}

// ── Fare summary ───────────────────────────────────────────────────
export function FareSummary({ request }: { request: RideRequest }) {
  const share = request.my_fare_share_inr;
  return (
    <Card elevated={false} style={{ backgroundColor: colors.surfaceAlt, borderWidth: 0 }}>
      <Row between>
        <View>
          <Caption>Your share</Caption>
          <H2 color={colors.primaryDark}>{share != null ? formatINR(share) : '—'}</H2>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Caption>Group total</Caption>
          <BodyBold>{formatINR(request.estimated_fare_total)}</BodyBold>
          <Small>{formatKm(request.route_distance_km)} · {formatMinutes(request.route_duration_min)}</Small>
        </View>
      </Row>
      {request.my_savings_inr ? (
        <View style={styles.savings}><SmallBold color="#15803D">You save {formatINR(request.my_savings_inr)} vs riding alone 🎉</SmallBold></View>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  vehicle: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderRadius: radii.lg, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface },
  dot: { width: 10, height: 10, borderRadius: 5 },
  actionBtn: { flex: 1, paddingVertical: 11, borderRadius: radii.md, alignItems: 'center' },
  codeCard: { borderRadius: radii.xl, padding: spacing.xl, alignItems: 'center' },
  radar: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.lg },
  radarRings: { width: 140, height: 140, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  ring: { position: 'absolute', width: 140, height: 140, borderRadius: 70, backgroundColor: colors.primary },
  radarCore: { width: 60, height: 60, borderRadius: 30, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: colors.primary },
  savings: { marginTop: spacing.md, backgroundColor: colors.successLight, borderRadius: radii.sm, paddingVertical: 8, paddingHorizontal: 10, alignSelf: 'flex-start' },
});
