import React from 'react';
import { FlatList, Pressable, ScrollView, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import { colors, formatDateTime, formatINR, formatKm, spacing } from '@traveo/shared';
import { Avatar, Body, BodyBold, Button, Caption, Card, Divider, Empty, H1, H3, Loading, Pill, Row, Screen, Small, Spacer } from '@traveo/mobile-ui';
import { API_URL } from '@/config';
import { api } from '@/lib/api';
import { useAuth } from '@/store/auth';
import type { AppStackParamList } from '@/navigation/types';

export function HistoryScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const q = useQuery({ queryKey: ['driver', 'history'], queryFn: async () => (await api.drivers.history(40)).data });
  return (
    <Screen padded={false}>
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>
        <Row gap={10}><Pressable onPress={() => navigation.goBack()}><BodyBold>←</BodyBold></Pressable><H1>Trip history</H1></Row>
      </View>
      <Spacer h={spacing.md} />
      {q.isLoading ? <Loading /> : (
        <FlatList
          data={q.data ?? []}
          keyExtractor={(r) => r.ride_id}
          contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 80, gap: spacing.sm }}
          renderItem={({ item }) => (
            <Card style={{ gap: 4 }}>
              <Row between>
                <BodyBold numberOfLines={1} style={{ flex: 1 }}>{item.origin_address?.split(',')[0]} → {item.destination_address?.split(',')[0]}</BodyBold>
                <Pill label={item.status} status={item.status} />
              </Row>
              <Row between>
                <Small>{formatDateTime(item.completed_at ?? item.cancelled_at)} · {item.vehicle_label} · {item.passengers} pax · {formatKm(item.total_distance_km)}</Small>
                <BodyBold color={colors.success}>{formatINR(item.driver_payout_inr)}</BodyBold>
              </Row>
            </Card>
          )}
          ListEmptyComponent={<Empty emoji="🧾" title="No trips yet" body="Go online and accept your first student group." />}
        />
      )}
    </Screen>
  );
}

export function ProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const user = useAuth((s) => s.user);
  const signOut = useAuth((s) => s.signOut);
  const d = user?.driver;
  return (
    <Screen padded={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 80 }}>
        <Row gap={10}><Pressable onPress={() => navigation.goBack()}><BodyBold>←</BodyBold></Pressable><H1>Profile</H1></Row>
        <Spacer h={spacing.lg} />
        <Row gap={14}>
          <Avatar name={user?.full_name || 'D'} size={64} color={colors.driver} />
          <View style={{ flex: 1 }}>
            <H3>{user?.full_name}</H3>
            <Small>{user?.phone}</Small>
            <Row gap={6} style={{ marginTop: 4 }}><Pill label={d?.verification_status ?? 'pending'} status={d?.verification_status ?? 'pending'} /><Small>★ {d?.average_rating.toFixed(1)} ({d?.rating_count})</Small></Row>
          </View>
        </Row>
        <Spacer h={spacing.lg} />
        <Card style={{ gap: 4 }}>
          <Caption>Vehicle</Caption>
          <BodyBold>{d?.vehicle?.make_model ?? '—'} · {d?.vehicle?.color ?? ''}</BodyBold>
          <Body>{d?.vehicle?.registration_number} · {d?.vehicle?.seat_capacity} seats · {d?.vehicle?.vehicle_type}</Body>
          <Divider />
          <Caption>Licence</Caption>
          <Body>{d?.license_number}</Body>
        </Card>
        <Spacer h={spacing.md} />
        <Row gap={spacing.md}>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{d?.completed_rides ?? 0}</H3><Caption>trips</Caption></Card>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{formatINR(d?.total_earnings_inr ?? 0, { compact: true })}</H3><Caption>earned</Caption></Card>
          <Card style={{ flex: 1, alignItems: 'center' }}><H3>{Math.round((d?.acceptance_rate ?? 1) * 100)}%</H3><Caption>acceptance</Caption></Card>
        </Row>
        <Spacer h={spacing.xl} />
        <Button title="Sign out" variant="ghost" onPress={signOut} />
        <Spacer h={spacing.md} />
        <Small center color={colors.textMuted}>Traveo Driver v2.0 · API {API_URL.replace(/^https?:\/\//, '')}</Small>
      </ScrollView>
    </Screen>
  );
}
