import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQuery } from '@tanstack/react-query';
import { colors, radii, spacing, type FeedItem, type Place } from '@traveo/shared';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useAuth } from '@/store/auth';
import { useActiveRide } from '@/hooks/useActiveRide';
import { PlaceSearch } from '@/components/ride/PlaceSearch';
import { RideCard } from '@/components/ride';
import type { AppStackParamList } from '@/navigation/types';
import { toast, Button, Card, Empty, H1, Loading, Row, Screen, Segmented, Small, SmallBold, Spacer } from '@traveo/mobile-ui';

export function FeedScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const user = useAuth((s) => s.user);
  const college = user!.student!.college;
  const campus: Place = useMemo(() => ({ lat: college.latitude, lng: college.longitude, address: college.address || college.name, name: college.short_name || college.name }), [college]);
  const [direction, setDirection] = useState<'from_college' | 'to_college'>('from_college');
  const [other, setOther] = useState<Place | null>(null);
  const [showFilter, setShowFilter] = useState(true);
  const { data: active } = useActiveRide();

  const pickup = direction === 'from_college' ? campus : other;
  const drop = direction === 'from_college' ? other : campus;
  const matched = !!other;

  const feed = useQuery({
    queryKey: ['feed', direction, other?.lat, other?.lng],
    queryFn: async () =>
      (
        await api.rides.feed(
          matched ? { pickup_lat: pickup!.lat, pickup_lng: pickup!.lng, drop_lat: drop!.lat, drop_lng: drop!.lng } : {},
        )
      ).data,
    refetchInterval: 20000,
  });

  const hide = useMutation({
    mutationFn: (id: string) => api.rides.hide(id),
    onMutate: async (id) => {
      queryClient.setQueriesData<FeedItem[]>({ queryKey: ['feed'] }, (old) => old?.filter((i) => i.request.id !== id));
    },
    onSuccess: () => toast('Hidden', "We won't show this ride again"),
  });

  const items = (feed.data ?? []).filter((i) => (matched ? true : i.request.direction === direction));

  return (
    <Screen padded={false}>
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>
        <Row between>
          <H1>Rides from {college.short_name || 'campus'}</H1>
          <Pressable onPress={() => setShowFilter((s) => !s)}><SmallBold color={colors.primary}>{showFilter ? 'Hide filters' : 'Filters'}</SmallBold></Pressable>
        </Row>
        <Small>Only students of {college.name} can see these.</Small>
        {showFilter ? (
          <Card elevated={false} style={{ marginTop: spacing.md, gap: spacing.md }}>
            <Segmented value={direction} onChange={(v) => { setDirection(v); setOther(null); }} options={[{ value: 'from_college', label: 'Leaving campus' }, { value: 'to_college', label: 'Going to campus' }]} />
            <PlaceSearch
              label={direction === 'from_college' ? 'Your destination (to rank by match)' : 'Your pickup point'}
              value={other}
              onChange={setOther}
              near={campus}
              placeholder="Type to match rides on your route"
              accent={direction === 'from_college' ? colors.drop : colors.pickup}
            />
          </Card>
        ) : null}
      </View>
      <Spacer h={spacing.md} />
      {feed.isLoading ? (
        <Loading label="Finding rides on your route…" />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(i) => i.request.id}
          contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 120, gap: spacing.md }}
          refreshControl={<RefreshControl refreshing={feed.isFetching} onRefresh={() => feed.refetch()} tintColor={colors.primary} />}
          renderItem={({ item }) => (
            <RideCard
              request={item.request}
              match={item.match}
              onPress={() => navigation.navigate('Ride', { requestId: item.request.id })}
              onReject={() => hide.mutate(item.request.id)}
              onAccept={() => {
                if (active) {
                  toast('You already have an active ride', 'Leave it first to join another', 'error');
                  return;
                }
                navigation.navigate('JoinRide', { requestId: item.request.id, pickup: pickup ?? undefined, drop: drop ?? undefined });
              }}
            />
          )}
          ListEmptyComponent={
            <Empty
              emoji="🧭"
              title={matched ? 'No rides match your route yet' : 'No open rides right now'}
              body={matched ? 'Try a nearby destination or post your own ride – classmates get notified instantly.' : 'Be the first: post a ride and classmates on your route will join.'}
              action={<Button title="Post a ride" onPress={() => navigation.navigate('CreateRide', other ? (direction === 'from_college' ? { destination: other } : { origin: other }) : undefined)} size="md" />}
            />
          }
        />
      )}
    </Screen>
  );
}

export const feedStyles = StyleSheet.create({ chip: { borderRadius: radii.pill } });
