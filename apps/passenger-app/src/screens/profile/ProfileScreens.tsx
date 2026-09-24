import React from 'react';
import { FlatList, Pressable, ScrollView, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQuery } from '@tanstack/react-query';
import { colors, formatDateTime, formatINR, spacing, STATUS_LABEL, timeAgo, type AppNotification } from '@traveo/shared';
import { API_URL } from '@/config';
import { api } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useAuth } from '@/store/auth';
import { useActiveRide } from '@/hooks/useActiveRide';
import { RideCard } from '@/components/ride';
import { Avatar, Body, BodyBold, Button, Caption, Card, Divider, Empty, H1, H3, Loading, Pill, Row, Screen, Small, SmallBold, Spacer } from '@traveo/mobile-ui';
import type { AppStackParamList } from '@/navigation/types';

export function ProfileScreen() {
  const user = useAuth((s) => s.user);
  const signOut = useAuth((s) => s.signOut);
  const refreshUser = useAuth((s) => s.refreshUser);
  const sp = user?.student;
  return (
    <Screen padded={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 100 }}>
        <Row gap={14}>
          <Avatar name={user?.full_name || 'S'} size={64} />
          <View style={{ flex: 1 }}>
            <H1 numberOfLines={1}>{user?.full_name}</H1>
            <Small>{user?.phone}</Small>
            <Row gap={6} style={{ marginTop: 4 }}>
              <Pill label={sp?.verification_status ?? 'pending'} status={sp?.verification_status ?? 'pending'} />
              <Small>★ {sp?.average_rating.toFixed(1)} ({sp?.rating_count})</Small>
            </Row>
          </View>
        </Row>
        <Spacer h={spacing.lg} />
        <Card style={{ gap: 6 }}>
          <Caption>Student identity</Caption>
          <BodyBold>{sp?.college.name}</BodyBold>
          <Small>ID {sp?.college_id_number} · “{sp?.college_name_on_id}” on card</Small>
          <Small>{sp?.course ?? '—'}{sp?.graduation_year ? ` · Class of ${sp.graduation_year}` : ''}</Small>
          <Divider />
          <Small>{sp?.verification_note}</Small>
          <Small color={colors.textMuted}>Identity match {Math.round((sp?.identity_match_score ?? 0) * 100)}%</Small>
        </Card>
        <Spacer h={spacing.md} />
        <Row gap={spacing.md}>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{sp?.completed_rides ?? 0}</H3><Caption>rides shared</Caption></Card>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{formatINR(sp?.total_saved_inr ?? 0)}</H3><Caption>saved</Caption></Card>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{((sp?.completed_rides ?? 0) * 1.9).toFixed(0)} kg</H3><Caption>CO₂ avoided</Caption></Card>
        </Row>
        <Spacer h={spacing.lg} />
        <Card style={{ gap: 4 }}>
          <Caption>How Traveo keeps you safe</Caption>
          <Small>• Only verified students of {sp?.college.short_name || 'your college'} see your rides</Small>
          <Small>• Ride lead holds the OTP; every co-rider has a matching ID the driver checks</Small>
          <Small>• Live location is shared with your group during the ride</Small>
          <Small>• Women-only rides available</Small>
        </Card>
        <Spacer h={spacing.lg} />
        <Button title="Refresh profile" variant="secondary" onPress={() => refreshUser()} />
        <Spacer h={spacing.sm} />
        <Button title="Sign out" variant="ghost" onPress={signOut} />
        <Spacer h={spacing.lg} />
        <Small center color={colors.textMuted}>Traveo v2.0 · API {API_URL.replace(/^https?:\/\//, '')}</Small>
      </ScrollView>
    </Screen>
  );
}

export function ActivityScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { data: active } = useActiveRide();
  const history = useQuery({ queryKey: ['rides', 'history'], queryFn: async () => (await api.rides.history(30)).data });
  const items = history.data ?? [];
  return (
    <Screen padded={false}>
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>
        <H1>Your rides</H1>
      </View>
      <Spacer h={spacing.md} />
      {history.isLoading ? <Loading /> : (
        <FlatList
          data={items}
          keyExtractor={(r) => r.id}
          contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 120, gap: spacing.md }}
          ListHeaderComponent={active ? (
            <View style={{ gap: spacing.sm, marginBottom: spacing.sm }}>
              <SmallBold>Active</SmallBold>
              <RideCard request={active} compact onPress={() => navigation.navigate('Ride', { requestId: active.id })} />
              <SmallBold style={{ marginTop: spacing.sm }}>Past rides</SmallBold>
            </View>
          ) : null}
          renderItem={({ item }) => (
            <Card onPress={() => navigation.navigate('Ride', { requestId: item.id })} style={{ gap: 6 }}>
              <Row between>
                <BodyBold numberOfLines={1} style={{ flex: 1 }}>{item.origin_address.split(',')[0]} → {item.destination_address.split(',')[0]}</BodyBold>
                <Pill label={STATUS_LABEL[item.status]} status={item.status} />
              </Row>
              <Row between>
                <Small>{formatDateTime(item.departure_at)} · {item.vehicle_label} · {item.members.length} rider{item.members.length === 1 ? '' : 's'}</Small>
                <BodyBold>{item.my_fare_share_inr != null ? formatINR(item.my_fare_share_inr) : ''}</BodyBold>
              </Row>
            </Card>
          )}
          ListEmptyComponent={!active ? <Empty emoji="🗺️" title="No rides yet" body="Post a ride or join a classmate's – your history shows up here." /> : null}
        />
      )}
    </Screen>
  );
}

export function NotificationsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const q = useQuery({ queryKey: ['notifications'], queryFn: async () => (await api.notifications.list(50)).data });
  const readAll = useMutation({ mutationFn: () => api.notifications.readAll(), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }) });
  const open = (n: AppNotification) => {
    const rid = n.data?.request_id as string | undefined;
    if (rid) navigation.navigate('Ride', { requestId: rid });
  };
  return (
    <Screen padded={false}>
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>
        <Row between>
          <Row gap={10}><Pressable onPress={() => navigation.goBack()}><BodyBold>←</BodyBold></Pressable><H1>Notifications</H1></Row>
          <Pressable onPress={() => readAll.mutate()}><Small color={colors.primary}>Mark all read</Small></Pressable>
        </Row>
      </View>
      <Spacer h={spacing.md} />
      <FlatList
        data={q.data ?? []}
        keyExtractor={(n) => n.id}
        contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 60, gap: spacing.sm }}
        renderItem={({ item }) => (
          <Card onPress={() => open(item)} style={{ opacity: item.is_read ? 0.7 : 1, gap: 2 }}>
            <Row between><BodyBold>{item.title}</BodyBold><Caption>{timeAgo(item.created_at)}</Caption></Row>
            <Body>{item.body}</Body>
          </Card>
        )}
        ListEmptyComponent={q.isLoading ? <Loading /> : <Empty emoji="🔔" title="All quiet" body="Ride updates and co-rider activity land here." />}
      />
      <Text />
    </Screen>
  );
}
