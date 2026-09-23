import React, { useEffect, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { ApiError, colors, radii, spacing, VEHICLES, type VehicleType } from '@traveo/shared';
import { Body, BodyBold, Button, Caption, Card, Display, H1, H2, Input, Pill, Row, Screen, Small, SmallBold, Spacer, toast } from '@traveo/mobile-ui';
import { api } from '@/lib/api';
import { useAuth } from '@/store/auth';
import type { AuthStackParamList } from '@/navigation/types';

export function WelcomeScreen({ navigation }: NativeStackScreenProps<AuthStackParamList, 'Welcome'>) {
  return (
    <LinearGradient colors={['#0369A1', colors.driver]} style={{ flex: 1 }}>
      <Screen style={{ backgroundColor: 'transparent', justifyContent: 'space-between', paddingBottom: spacing.xxl }} edges={['top', 'bottom']}>
        <View style={{ marginTop: spacing.xxxl }}>
          <Text style={{ fontSize: 56 }}>🚕</Text>
          <Display color="#fff" style={{ marginTop: spacing.lg }}>Traveo Driver</Display>
          <H2 color="#E0F2FE">Full rides, verified students, zero haggling.</H2>
          <Spacer h={spacing.xl} />
          {[
            ['👥', 'Groups of students already matched – more fare per trip'],
            ['📍', 'Optimised pickup order, campus gates as hubs'],
            ['🔐', 'OTP + matching codes: you always know who boards'],
          ].map(([e, t]) => (
            <Row key={t} gap={12} style={{ marginBottom: spacing.md }}>
              <Text style={{ fontSize: 22 }}>{e}</Text>
              <Body color="#E0F2FE" style={{ flex: 1 }}>{t}</Body>
            </Row>
          ))}
        </View>
        <Button title="Continue with phone number" variant="accent" onPress={() => navigation.navigate('Phone')} />
      </Screen>
    </LinearGradient>
  );
}

export function PhoneScreen({ navigation }: NativeStackScreenProps<AuthStackParamList, 'Phone'>) {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.auth.requestOtp(phone, 'driver');
      navigation.navigate('Otp', { phone: res.data.phone, devOtp: res.data.dev_otp ?? null });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not send OTP');
    } finally {
      setLoading(false);
    }
  };
  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <Spacer h={spacing.xxl} />
        <H1>Driver sign in</H1>
        <Small>Use the mobile number registered with Traveo.</Small>
        <Spacer h={spacing.xl} />
        <Input label="Mobile number" keyboardType="phone-pad" placeholder="99000 00001" value={phone} onChangeText={setPhone} autoFocus error={error} right={<SmallBold color={colors.textMuted}>+91</SmallBold>} />
        <Spacer h={spacing.xl} />
        <Button title="Send OTP" onPress={submit} loading={loading} disabled={!/^\+?\d{10,13}$/.test(phone.replace(/\s/g, ''))} />
      </KeyboardAvoidingView>
    </Screen>
  );
}

export function OtpScreen({ route, navigation }: NativeStackScreenProps<AuthStackParamList, 'Otp'>) {
  const { phone, devOtp } = route.params;
  const [otp, setOtp] = useState(devOtp ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const completeLogin = useAuth((s) => s.completeLogin);
  const inputRef = useRef<TextInput>(null);
  const verify = async (code = otp) => {
    if (code.length < 4) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.auth.verifyOtp(phone, code, 'driver');
      await completeLogin(res.data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };
  return (
    <Screen>
      <Spacer h={spacing.xxl} />
      <H1>Enter the code</H1>
      <Small>Sent to {phone}.{devOtp ? ' Development mode: pre-filled.' : ''}</Small>
      <Spacer h={spacing.xl} />
      <Pressable onPress={() => inputRef.current?.focus()} style={styles.otpRow}>
        {Array.from({ length: 6 }).map((_, i) => (
          <View key={i} style={[styles.otpCell, otp.length === i && { borderColor: colors.driver }]}><H2>{otp[i] ?? ''}</H2></View>
        ))}
      </Pressable>
      <TextInput ref={inputRef} value={otp} onChangeText={(t) => { const c = t.replace(/\D/g, '').slice(0, 6); setOtp(c); if (c.length === 6) verify(c); }} keyboardType="number-pad" autoFocus style={{ position: 'absolute', opacity: 0, height: 1, width: 1 }} />
      {error ? <Small color={colors.danger} style={{ marginTop: spacing.sm }}>{error}</Small> : null}
      <Spacer h={spacing.xl} />
      <Button title="Verify" onPress={() => verify()} loading={loading} disabled={otp.length < 4} />
      <Spacer h={spacing.md} />
      <Pressable onPress={() => navigation.goBack()}><Small color={colors.driver}>Change number</Small></Pressable>
    </Screen>
  );
}

export function RegisterScreen() {
  const [name, setName] = useState('');
  const [license, setLicense] = useState('');
  const [vehicle, setVehicle] = useState<VehicleType>('auto');
  const [reg, setReg] = useState('');
  const [model, setModel] = useState('');
  const [color, setColor] = useState('');
  const [loading, setLoading] = useState(false);
  const setUser = useAuth((s) => s.setUser);
  const signOut = useAuth((s) => s.signOut);
  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.drivers.register({ full_name: name.trim(), license_number: license.trim(), vehicle_type: vehicle, registration_number: reg.trim(), make_model: model.trim() || undefined, color: color.trim() || undefined });
      setUser(res.data);
      toast('Profile created', res.data.driver?.verification_status === 'verified' ? 'You can go online now.' : 'Pending verification by Traveo ops.', 'success');
    } catch (e) {
      toast('Could not register', e instanceof ApiError ? e.message : undefined, 'error');
    } finally {
      setLoading(false);
    }
  };
  return (
    <Screen padded={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 60 }} keyboardShouldPersistTaps="handled">
        <Spacer h={spacing.md} />
        <H1>Set up your driver profile</H1>
        <Small>Your licence and vehicle are verified by the Traveo team.</Small>
        <Spacer h={spacing.xl} />
        <Input label="Full name" value={name} onChangeText={setName} placeholder="As on your licence" />
        <Spacer h={spacing.lg} />
        <Input label="Driving licence number" value={license} onChangeText={(t) => setLicense(t.toUpperCase())} autoCapitalize="characters" placeholder="MH1220190012345" />
        <Spacer h={spacing.lg} />
        <SmallBold color={colors.textSecondary} style={{ marginBottom: 6 }}>Vehicle type</SmallBold>
        <View style={{ gap: spacing.sm }}>
          {VEHICLES.map((v) => (
            <Pressable key={v.type} onPress={() => setVehicle(v.type)} style={[styles.vehicle, vehicle === v.type && { borderColor: colors.driver, backgroundColor: colors.infoLight }]}>
              <Text style={{ fontSize: 26 }}>{v.emoji}</Text>
              <View style={{ flex: 1 }}><BodyBold>{v.label}</BodyBold><Small>{v.capacity} passenger seats</Small></View>
            </Pressable>
          ))}
        </View>
        <Spacer h={spacing.lg} />
        <Input label="Registration number" value={reg} onChangeText={(t) => setReg(t.toUpperCase())} autoCapitalize="characters" placeholder="MH12AB1234" />
        <Spacer h={spacing.lg} />
        <Row gap={spacing.md}>
          <View style={{ flex: 1 }}><Input label="Make & model" value={model} onChangeText={setModel} placeholder="Maruti Dzire" /></View>
          <View style={{ flex: 1 }}><Input label="Colour" value={color} onChangeText={setColor} placeholder="White" /></View>
        </Row>
        <Spacer h={spacing.xl} />
        <Button title="Create driver profile" onPress={submit} loading={loading} disabled={name.trim().length < 2 || license.trim().length < 6 || reg.trim().length < 6} />
        <Spacer h={spacing.md} />
        <Pressable onPress={signOut}><Small center color={colors.textMuted}>Use a different number</Small></Pressable>
      </ScrollView>
    </Screen>
  );
}

export function PendingScreen() {
  const user = useAuth((s) => s.user);
  const refreshUser = useAuth((s) => s.refreshUser);
  const signOut = useAuth((s) => s.signOut);
  const status = user?.driver?.verification_status;
  const note = user?.driver?.verification_note;

  useEffect(() => {
    const t = setInterval(() => refreshUser(), 10000);
    return () => clearInterval(t);
  }, [refreshUser]);

  const isRejected = (status === 'rejected');

  return (
    <Screen style={{ justifyContent: 'center' }}>
      <Card style={{ alignItems: 'center', gap: spacing.md, maxWidth: 440, width: '100%', alignSelf: 'center' }}>
        <Text style={{ fontSize: 52 }}>{isRejected ? '⛔' : '🕒'}</Text>
        <H2 center>{isRejected ? 'Application Rejected' : 'Profile in Review'}</H2>
        <Small center color={colors.textSecondary} style={{ fontWeight: '600' }}>
          {isRejected
            ? 'Admin could not verify your driver licence or vehicle registration.'
            : 'Please wait for 10 minutes while admin verifies your licence and vehicle details.'}
        </Small>

        {/* Reason / status notes card */}
        <View style={{ width: '100%', backgroundColor: isRejected ? '#FEE2E2' : colors.surfaceAlt, padding: spacing.md, borderRadius: radii.md, borderWidth: 1, borderColor: isRejected ? '#FCA5A5' : colors.border }}>
          <Caption color={isRejected ? '#991B1B' : colors.textMuted}>
            {isRejected ? 'REASON FOR REJECTION' : 'STATUS NOTE'}
          </Caption>
          <SmallBold color={isRejected ? '#B91C1C' : colors.text} style={{ marginTop: 2 }}>
            {note || (isRejected ? 'Licence or vehicle verification failed. Contact admin support.' : `Traveo ops is reviewing licence ${user?.driver?.license_number || ''} and vehicle ${user?.driver?.vehicle?.registration_number || ''}.`)}
          </SmallBold>
        </View>

        <Row gap={8} style={{ alignItems: 'center', marginVertical: 4 }}>
          <Pill label={status ?? 'pending'} status={status ?? 'pending'} />
          <Caption>{user?.driver?.vehicle?.registration_number || 'Vehicle'}</Caption>
        </Row>

        <Button title="Refresh Status" variant="secondary" onPress={() => refreshUser()} style={{ alignSelf: 'stretch' }} />
        <Pressable onPress={signOut} style={{ marginTop: spacing.xs }}><Small color={colors.textMuted}>Sign out / Use a different number</Small></Pressable>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  otpRow: { flexDirection: 'row', gap: 8 },
  otpCell: { flex: 1, height: 56, borderRadius: radii.md, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  vehicle: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 12, borderRadius: radii.lg, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface },
});
