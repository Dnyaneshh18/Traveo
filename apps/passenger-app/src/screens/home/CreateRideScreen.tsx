import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ApiError, colors, decodePolyline, formatINR, formatKm, formatMinutes, radii, spacing, VEHICLE_BY_TYPE, type LatLng, type Place, type VehicleType } from '@traveo/shared';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useAuth } from '@/store/auth';
import { PlaceSearch } from '@/components/ride/PlaceSearch';
import { VehiclePicker } from '@/components/ride';
import type { AppStackParamList } from '@/navigation/types';
import { toast, MapView, type MapMarker, Body, BodyBold, Button, Caption, Card, H1, H3, Input, Row, Screen, Segmented, Small, SmallBold, Spacer, Stepper } from '@traveo/mobile-ui';

type Props = NativeStackScreenProps<AppStackParamList, 'CreateRide'>;

const DEPARTURE_OPTIONS = [
  { label: 'Now', minutes: 10 },
  { label: '+20 min', minutes: 20 },
  { label: '+45 min', minutes: 45 },
  { label: '+1.5 h', minutes: 90 },
];

export function CreateRideScreen({ navigation, route }: Props) {
  const user = useAuth((s) => s.user);
  const college = user!.student!.college;
  const campus: Place = useMemo(() => ({ lat: college.latitude, lng: college.longitude, address: college.address || college.name, name: college.short_name || college.name }), [college]);

  const [direction, setDirection] = useState<'from_college' | 'to_college'>('from_college');
  const [other, setOther] = useState<Place | null>(route.params?.destination ?? null);
  const [vehicle, setVehicle] = useState<VehicleType>('auto');
  const [seats, setSeats] = useState(1);
  const [departureMin, setDepartureMin] = useState(10);
  const [note, setNote] = useState('');
  const [womenOnly, setWomenOnly] = useState(false);

  const origin = direction === 'from_college' ? campus : other;
  const destination = direction === 'from_college' ? other : campus;

  const preview = useQuery({
    queryKey: ['preview', origin?.lat, origin?.lng, destination?.lat, destination?.lng],
    queryFn: async () => (await api.rides.preview(origin!, destination!)).data,
    enabled: !!origin && !!destination,
  });

  useEffect(() => {
    if (seats > VEHICLE_BY_TYPE[vehicle].capacity) setSeats(VEHICLE_BY_TYPE[vehicle].capacity);
  }, [vehicle, seats]);

  const create = useMutation({
    mutationFn: async () =>
      (
        await api.rides.create({
          origin: origin!,
          destination: destination!,
          vehicle_type: vehicle,
          seats,
          departure_at: new Date(Date.now() + departureMin * 60000).toISOString(),
          note: note.trim() || null,
          women_only: womenOnly,
        })
      ).data,
    onSuccess: (req) => {
      queryClient.invalidateQueries({ queryKey: ['rides'] });
      toast('Ride published 🎉', 'Classmates on your route can now join.', 'success');
      navigation.replace('Ride', { requestId: req.id });
    },
    onError: (e) => toast('Could not publish', e instanceof ApiError ? e.message : undefined, 'error'),
  });

  const polyline = preview.data?.polyline ? decodePolyline(preview.data.polyline) : undefined;
  const markers = useMemo<MapMarker[]>(() => {
    const m: MapMarker[] = [{ id: 'campus', lat: campus.lat, lng: campus.lng, kind: 'campus' }];
    if (other) m.push({ id: 'other', lat: other.lat, lng: other.lng, kind: direction === 'from_college' ? 'drop' : 'pickup' });
    return m;
  }, [campus, other, direction]);
  const fitTo = useMemo<LatLng[]>(() => (other ? [campus, other] : [campus]), [campus, other]);
  const selected = preview.data?.options.find((o) => o.vehicle_type === vehicle);
  const canSubmit = !!origin && !!destination && !!preview.data && !create.isPending;

  return (
    <Screen padded={false} edges={['top']}>
      <View style={{ height: 220 }}>
        <MapView markers={markers} polyline={polyline} fitTo={fitTo} interactive={false} />
        <Pressable onPress={() => navigation.goBack()} style={styles.back}><BodyBold>←</BodyBold></Pressable>
      </View>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 140 }} keyboardShouldPersistTaps="handled">
        <H1>Post a ride</H1>
        <Small>Only verified {college.short_name || college.name} students will see it.</Small>
        <Spacer h={spacing.lg} />
        <Segmented
          value={direction}
          onChange={(v) => setDirection(v)}
          options={[
            { value: 'from_college', label: `Leaving ${college.short_name || 'campus'}` },
            { value: 'to_college', label: `Going to ${college.short_name || 'campus'}` },
          ]}
        />
        <Spacer h={spacing.lg} />
        <Card elevated={false} style={{ gap: spacing.md }}>
          <Row gap={10}>
            <View style={[styles.dot, { backgroundColor: colors.pickup }]} />
            <View style={{ flex: 1 }}>
              <Caption>{direction === 'from_college' ? 'Pickup' : 'Drop'}</Caption>
              <BodyBold numberOfLines={1}>{campus.name}</BodyBold>
              <Small numberOfLines={1}>{campus.address}</Small>
            </View>
          </Row>
          <PlaceSearch
            label={direction === 'from_college' ? 'Where to?' : 'Where from?'}
            value={other}
            onChange={setOther}
            near={campus}
            placeholder={direction === 'from_college' ? 'Home, hostel, station…' : 'Your pickup point'}
            accent={direction === 'from_college' ? colors.drop : colors.pickup}
          />
        </Card>
        <Spacer h={spacing.lg} />

        {preview.data ? (
          <Card elevated={false} style={{ backgroundColor: colors.primaryLight, borderWidth: 0 }}>
            <Row between>
              <View><Caption>Route</Caption><BodyBold>{formatKm(preview.data.distance_km)} · {formatMinutes(preview.data.duration_min)}</BodyBold></View>
              <View style={{ alignItems: 'flex-end' }}><Caption>via</Caption><SmallBold>{preview.data.provider === 'mappls' ? 'Mappls routing' : 'estimated'}</SmallBold></View>
            </Row>
          </Card>
        ) : preview.isFetching ? <Small>Calculating route…</Small> : null}
        <Spacer h={spacing.lg} />

        <H3>Vehicle</H3>
        <Small style={{ marginBottom: spacing.sm }}>Fare is split by distance. You can leave before it's full.</Small>
        <VehiclePicker value={vehicle} onChange={setVehicle} options={preview.data?.options} seats={seats} />
        <Spacer h={spacing.lg} />

        <Row between>
          <View><H3>Seats you need</H3><Small>Bringing friends along?</Small></View>
          <Stepper value={seats} min={1} max={Math.min(5, VEHICLE_BY_TYPE[vehicle].capacity)} onChange={setSeats} />
        </Row>
        <Spacer h={spacing.lg} />

        <H3>Leaving</H3>
        <Row gap={spacing.sm} style={{ marginTop: spacing.sm, flexWrap: 'wrap' }}>
          {DEPARTURE_OPTIONS.map((o) => (
            <Pressable key={o.label} onPress={() => setDepartureMin(o.minutes)} style={[styles.chip, departureMin === o.minutes && { backgroundColor: colors.primary, borderColor: colors.primary }]}>
              <SmallBold color={departureMin === o.minutes ? '#fff' : colors.textSecondary}>{o.label}</SmallBold>
            </Pressable>
          ))}
        </Row>
        <Spacer h={spacing.lg} />
        <Input label="Note for co-riders (optional)" value={note} onChangeText={setNote} placeholder="e.g. Leaving right after the 5pm lecture, gate 2" maxLength={200} />
        <Spacer h={spacing.lg} />
        {user?.student?.gender === 'female' ? (
          <Row between>
            <View style={{ flex: 1 }}><BodyBold>Women-only ride</BodyBold><Small>Only women from your college can join</Small></View>
            <Switch value={womenOnly} onValueChange={setWomenOnly} trackColor={{ true: colors.primary }} />
          </Row>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <View style={{ flex: 1 }}>
          <Caption>Estimated · {selected ? VEHICLE_BY_TYPE[selected.vehicle_type].label : ''}</Caption>
          <Row gap={6}>
            <H3 color={colors.primaryDark}>{selected ? formatINR(selected.per_seat_if_full) : '—'}</H3>
            <Small>per seat if full · {selected ? formatINR(selected.total_estimate) : '—'} total</Small>
          </Row>
        </View>
        <Button title="Publish ride" onPress={() => create.mutate()} loading={create.isPending} disabled={!canSubmit} style={{ paddingHorizontal: 24 }} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { position: 'absolute', top: 12, left: 12, width: 40, height: 40, borderRadius: 20, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  dot: { width: 10, height: 10, borderRadius: 5 },
  chip: { paddingHorizontal: 14, paddingVertical: 9, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.lg, paddingBottom: spacing.xl, backgroundColor: colors.surface, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
});
