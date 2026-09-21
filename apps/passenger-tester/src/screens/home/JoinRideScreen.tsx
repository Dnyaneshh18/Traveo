import React, { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useMutation } from '@tanstack/react-query';
import { ApiError, colors, decodePolyline, formatINR, spacing, type LatLng, type Place } from '@traveo/shared';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useAuth } from '@/store/auth';
import { useRideDetail } from '@/hooks/useActiveRide';
import { PlaceSearch } from '@/components/ride/PlaceSearch';
import { MemberRow, RideCard } from '@/components/ride';
import type { AppStackParamList } from '@/navigation/types';
import { toast, MapView, type MapMarker, Body, Button, Card, H1, H3, Loading, Row, Screen, Small, Spacer, Stepper } from '@traveo/mobile-ui';

type Props = NativeStackScreenProps<AppStackParamList, 'JoinRide'>;

export function JoinRideScreen({ navigation, route }: Props) {
  const { requestId } = route.params;
  const user = useAuth((s) => s.user);
  const college = user!.student!.college;
  const campus: Place = useMemo(() => ({ lat: college.latitude, lng: college.longitude, address: college.address || college.name, name: college.short_name || college.name }), [college]);
  const detail = useRideDetail(requestId);
  const req = detail.data;
  const fromCollege = req?.direction === 'from_college';
  const [other, setOther] = useState<Place | null>((fromCollege ? route.params.drop : route.params.pickup) ?? null);
  const [seats, setSeats] = useState(1);

  const pickup = fromCollege ? campus : other;
  const drop = fromCollege ? other : campus;

  const join = useMutation({
    mutationFn: async () => (await api.rides.join(requestId, { pickup: pickup!, drop: drop!, seats })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rides'] });
      queryClient.invalidateQueries({ queryKey: ['feed'] });
      toast("You're in! 🎉", 'The ride lead has been notified.', 'success');
      navigation.replace('Ride', { requestId });
    },
    onError: (e) => {
      const err = e instanceof ApiError ? e : null;
      const detail = err?.details as any;
      toast(
        err?.code === 'route_not_compatible' ? 'Too far from this route' : 'Could not join',
        err?.code === 'route_not_compatible' && detail?.detour_km != null ? `That would add ~${detail.detour_km} km detour. Try a closer stop.` : err?.message,
        'error',
      );
    },
  });

  if (!req) return <Screen><Loading label="Loading ride…" /></Screen>;

  const polyline = req.route_polyline ? decodePolyline(req.route_polyline) : undefined;
  const markers: MapMarker[] = [
    { id: 'o', lat: req.origin_lat, lng: req.origin_lng, kind: fromCollege ? 'campus' : 'pickup' },
    { id: 'd', lat: req.destination_lat, lng: req.destination_lng, kind: fromCollege ? 'drop' : 'campus' },
  ];
  if (other) markers.push({ id: 'me', lat: other.lat, lng: other.lng, kind: fromCollege ? 'drop' : 'pickup', label: 'You', color: colors.rider });
  const fitTo: LatLng[] = [...(polyline ?? [markers[0], markers[1]]), ...(other ? [other] : [])];

  return (
    <Screen padded={false} edges={['top']}>
      <View style={{ height: 240 }}>
        <MapView markers={markers} polyline={polyline} fitTo={fitTo} interactive={false} />
      </View>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 120 }} keyboardShouldPersistTaps="handled">
        <H1>Join this ride</H1>
        <Small>Set where you'll {fromCollege ? 'get off' : 'get picked up'} – the fare share updates by distance.</Small>
        <Spacer h={spacing.md} />
        <RideCard request={req} compact />
        <Spacer h={spacing.lg} />
        <Card elevated={false} style={{ gap: spacing.md }}>
          <PlaceSearch
            label={fromCollege ? 'Your drop point' : 'Your pickup point'}
            value={other}
            onChange={setOther}
            near={{ lat: fromCollege ? req.destination_lat : req.origin_lat, lng: fromCollege ? req.destination_lng : req.origin_lng }}
            placeholder="Somewhere along the route"
            accent={fromCollege ? colors.drop : colors.pickup}
          />
          <Row between>
            <View><Body>Seats</Body><Small>{req.seats_available} available</Small></View>
            <Stepper value={seats} min={1} max={Math.min(4, req.seats_available)} onChange={setSeats} />
          </Row>
        </Card>
        <Spacer h={spacing.lg} />
        <H3>Who's riding</H3>
        {req.members.filter((m) => m.status === 'accepted' || m.status === 'picked_up').map((m) => <MemberRow key={m.id} member={m} />)}
        <Spacer h={spacing.md} />
        <Small>Your matching ID is generated when you join. Only the ride lead holds the OTP; you show your ID to the driver.</Small>
      </ScrollView>
      <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: spacing.lg, paddingBottom: spacing.xl, backgroundColor: colors.surface }}>
        <Button
          title={other ? `Accept & join · est. ${formatINR(req.estimated_fare_total ? Math.round(req.estimated_fare_total / (req.seats_taken + seats)) : null)}` : 'Choose your stop to continue'}
          onPress={() => join.mutate()}
          loading={join.isPending}
          disabled={!other}
        />
      </View>
    </Screen>
  );
}
