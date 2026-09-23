import React, { useEffect, useMemo, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { ApiError, colors, radii, spacing, type College, type Gender } from '@traveo/shared';
import { api } from '@/lib/api';
import { useAuth } from '@/store/auth';
import type { AuthStackParamList } from '@/navigation/types';
import { toast, Body, BodyBold, Button, Caption, Card, Display, H1, H2, Input, Pill, Row, Screen, Small, SmallBold, Spacer } from '@traveo/mobile-ui';

// ── Welcome & Sign In ──────────────────────────────────────────────
export function WelcomeScreen({ navigation }: NativeStackScreenProps<AuthStackParamList, 'Welcome'>) {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const completeLogin = useAuth((s) => s.completeLogin);

  const validPhone = /^\d{10}$/.test(phone.replace(/\D/g, ''));

  const sendOtp = async () => {
    if (!validPhone) return;
    setLoading(true);
    setError(null);
    try {
      const cleanPhone = phone.replace(/\D/g, '');
      const res = await api.auth.requestOtp(cleanPhone, 'student');
      setDevOtp(res.data.dev_otp ?? null);
      if (res.data.dev_otp) {
        setOtp(res.data.dev_otp);
      }
      setStep('otp');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not send OTP');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    const cleanOtp = otp.trim();
    if (cleanOtp.length < 4) return;
    setLoading(true);
    setError(null);
    try {
      const cleanPhone = phone.replace(/\D/g, '');
      const res = await api.auth.verifyOtp(cleanPhone, cleanOtp, 'student');
      await completeLogin(res.data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: colors.primaryDark }}>
      <LinearGradient colors={[colors.primaryDark, colors.primary]} style={{ flex: 1, width: '100%' }}>
        <Screen style={{ backgroundColor: 'transparent', justifyContent: 'space-between', paddingBottom: spacing.xl }} edges={['top', 'bottom']}>
          <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ flexGrow: 1, justifyContent: 'space-between' }}>
            <View style={{ marginTop: spacing.xl }}>
              <Text style={{ fontSize: 48 }}>🎓🛺</Text>
              <Display color="#fff" style={{ marginTop: spacing.sm }}>Traveo</Display>
              <H2 color="#C7D2FE">Share rides with people from your own college.</H2>
              <Spacer h={spacing.lg} />
              {[
                ['🔒', 'Verified students only — same college, same route'],
                ['🤝', 'Post a ride, classmates accept, leave when you want'],
                ['🚕', 'Driver assigned & fare split fairly automatically'],
              ].map(([e, t]) => (
                <Row key={t} gap={12} style={{ marginBottom: spacing.sm }}>
                  <Text style={{ fontSize: 20 }}>{e}</Text>
                  <Body color="#E0E7FF" style={{ flex: 1 }}>{t}</Body>
                </Row>
              ))}
            </View>

            <Card style={{ backgroundColor: '#ffffff', marginTop: spacing.xl, padding: spacing.lg, borderRadius: radii.xl }}>
              {step === 'phone' ? (
                <View style={{ gap: spacing.md }}>
                  <View>
                    <H2 color={colors.text}>Student Sign In</H2>
                    <Small color={colors.textSecondary}>Enter your 10-digit mobile number to begin.</Small>
                  </View>
                  <Input
                    keyboardType="phone-pad"
                    placeholder="98765 43210"
                    value={phone}
                    onChangeText={(t) => { setPhone(t); setError(null); }}
                    autoFocus
                    maxLength={14}
                    error={error}
                    right={<SmallBold color={colors.textMuted}>+91</SmallBold>}
                  />
                  <Button
                    title="Send OTP"
                    variant="primary"
                    onPress={sendOtp}
                    loading={loading}
                    disabled={!validPhone}
                  />
                </View>
              ) : (
                <View style={{ gap: spacing.md }}>
                  <View>
                    <H2 color={colors.text}>Verify OTP</H2>
                    <Small color={colors.textSecondary}>
                      Enter the 6-digit code sent to +91 {phone}. {devOtp ? `(Dev code: ${devOtp})` : ''}
                    </Small>
                  </View>
                  <Input
                    keyboardType="number-pad"
                    placeholder="Enter OTP"
                    value={otp}
                    onChangeText={(t) => { setOtp(t); setError(null); }}
                    autoFocus
                    maxLength={6}
                    error={error}
                  />
                  <Button
                    title="Verify & Enter"
                    variant="primary"
                    onPress={verifyOtp}
                    loading={loading}
                    disabled={otp.length < 4}
                  />
                  <Row between>
                    <Pressable onPress={() => { setStep('phone'); setOtp(''); setError(null); }}>
                      <Small color={colors.primary}>← Change number</Small>
                    </Pressable>
                    <Pressable onPress={sendOtp}>
                      <Small color={colors.primary}>Resend OTP</Small>
                    </Pressable>
                  </Row>
                </View>
              )}
            </Card>

            <Small color="#C7D2FE" center style={{ marginTop: spacing.lg }}>
              By signing in you agree to Traveo's student community rules.
            </Small>
          </ScrollView>
        </Screen>
      </LinearGradient>
    </View>
  );
}

// ── Phone ──────────────────────────────────────────────────────────
export function PhoneScreen({ navigation }: NativeStackScreenProps<AuthStackParamList, 'Phone'>) {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valid = /^\d{10}$/.test(phone.replace(/\D/g, ''));

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.auth.requestOtp(phone, 'student');
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
        <H1>What's your number?</H1>
        <Small>We'll text you a one-time code. Students sign in with their mobile number.</Small>
        <Spacer h={spacing.xl} />
        <Input
          label="Mobile number"
          keyboardType="phone-pad"
          placeholder="98765 43210"
          value={phone}
          onChangeText={setPhone}
          autoFocus
          maxLength={13}
          error={error}
          right={<SmallBold color={colors.textMuted}>+91</SmallBold>}
        />
        <Spacer h={spacing.xl} />
        <Button title="Send OTP" onPress={submit} loading={loading} disabled={!valid} />
      </KeyboardAvoidingView>
    </Screen>
  );
}

// ── OTP ────────────────────────────────────────────────────────────
export function OtpScreen({ route, navigation }: NativeStackScreenProps<AuthStackParamList, 'Otp'>) {
  const { phone, devOtp } = route.params;
  const [otp, setOtp] = useState(devOtp ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(30);
  const completeLogin = useAuth((s) => s.completeLogin);
  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const verify = async (code = otp) => {
    if (code.length < 4) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.auth.verifyOtp(phone, code, 'student');
      await completeLogin(res.data);
      // RootNavigator switches to Register (no profile) or the app.
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    try {
      const res = await api.auth.requestOtp(phone, 'student');
      setCooldown(30);
      if (res.data.dev_otp) setOtp(res.data.dev_otp);
      toast('OTP sent again');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not resend');
    }
  };

  return (
    <Screen>
      <Spacer h={spacing.xxl} />
      <H1>Enter the code</H1>
      <Small>Sent to {phone}. {devOtp ? 'Development mode: the code is pre-filled.' : ''}</Small>
      <Spacer h={spacing.xl} />
      <Pressable onPress={() => inputRef.current?.focus()} style={styles.otpRow}>
        {Array.from({ length: 6 }).map((_, i) => (
          <View key={i} style={[styles.otpCell, otp.length === i && { borderColor: colors.primary }]}>
            <H2>{otp[i] ?? ''}</H2>
          </View>
        ))}
      </Pressable>
      <TextInput
        ref={inputRef}
        value={otp}
        onChangeText={(t) => {
          const clean = t.replace(/\D/g, '').slice(0, 6);
          setOtp(clean);
          if (clean.length === 6) verify(clean);
        }}
        keyboardType="number-pad"
        autoFocus
        style={{ position: 'absolute', opacity: 0, height: 1, width: 1 }}
      />
      {error ? <Small color={colors.danger} style={{ marginTop: spacing.sm }}>{error}</Small> : null}
      <Spacer h={spacing.xl} />
      <Button title="Verify" onPress={() => verify()} loading={loading} disabled={otp.length < 4} />
      <Spacer h={spacing.md} />
      <Row between>
        <Pressable onPress={() => navigation.goBack()}><Small color={colors.primary}>Change number</Small></Pressable>
        <Pressable onPress={resend} disabled={cooldown > 0}><Small color={cooldown > 0 ? colors.textMuted : colors.primary}>{cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}</Small></Pressable>
      </Row>
    </Screen>
  );
}

// ── Register (college identity) ────────────────────────────────────
export function RegisterScreen({ navigation }: any) {
  const [name, setName] = useState('');
  const [query, setQuery] = useState('');
  const [colleges, setColleges] = useState<College[]>([]);
  const [college, setCollege] = useState<College | null>(null);
  const [nameOnId, setNameOnId] = useState('');
  const [idNumber, setIdNumber] = useState('');
  const [gender, setGender] = useState<Gender | null>(null);
  const [course, setCourse] = useState('');
  const [preview, setPreview] = useState<{ name_matches: boolean; name_score: number; id_format_valid: boolean; auto_verified: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const status = useAuth((s) => s.status);
  const setUser = useAuth((s) => s.setUser);
  const signOut = useAuth((s) => s.signOut);

  // If session is not signed in, prompt user to sign in
  const isSessionValid = status === 'signed_in';

  useEffect(() => {
    let cancelled = false;
    api.colleges.search(query || undefined).then((r) => !cancelled && setColleges(r.data)).catch(() => {});
    return () => { cancelled = true; };
  }, [query]);

  // Live identity check (debounced) – explains the rule before submitting.
  useEffect(() => {
    if (!college || nameOnId.trim().length < 3 || idNumber.trim().length < 3) {
      setPreview(null);
      return;
    }
    const t = setTimeout(() => {
      api.students.identityPreview({ college_id: college.id, college_name_on_id: nameOnId.trim(), college_id_number: idNumber.trim() })
        .then((r) => setPreview(r.data))
        .catch(() => setPreview(null));
    }, 350);
    return () => clearTimeout(t);
  }, [college?.id, nameOnId, idNumber]);

  const canSubmit = name.trim().length >= 2 && !!college && nameOnId.trim().length >= 3 && idNumber.trim().length >= 3 && (preview?.name_matches ?? true);

  const submit = async () => {
    if (!college) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.students.register({
        full_name: name.trim(),
        college_id: college.id,
        college_name_on_id: nameOnId.trim(),
        college_id_number: idNumber.trim(),
        gender,
        course: course.trim() || null,
      });
      setUser(res.data);
      toast(res.data.student?.verification_status === 'verified' ? 'Identity verified ✅' : 'Profile created', res.data.student?.verification_note ?? undefined, 'success');
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setError('Your session has expired. Please sign in with your phone number.');
        toast('Session expired', 'Please sign in again.', 'error');
        await signOut();
        return;
      }
      const msg = e instanceof ApiError ? e.message : 'Registration failed';
      setError(msg);
      toast('Could not verify', msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const genders: { value: Gender; label: string }[] = [
    { value: 'female', label: 'Woman' },
    { value: 'male', label: 'Man' },
    { value: 'other', label: 'Other' },
  ];

  return (
    <Screen padded={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 60 }} keyboardShouldPersistTaps="handled">
        <Spacer h={spacing.md} />
        <H1>Verify your student identity</H1>
        <Small>Traveo is a closed campus network. Only verified students of your college can see your rides.</Small>
        <Spacer h={spacing.xl} />

        <Input label="Full name" value={name} onChangeText={setName} placeholder="As on your ID card" />
        <Spacer h={spacing.lg} />

        <SmallBold color={colors.textSecondary} style={{ marginBottom: 6 }}>Your college / school</SmallBold>
        {college ? (
          <Card elevated={false} style={{ borderColor: colors.primary, backgroundColor: colors.primaryLight }}>
            <Row between>
              <View style={{ flex: 1 }}>
                <BodyBold>{college.name}</BodyBold>
                <Small>{college.city} · {college.institution_type}</Small>
              </View>
              <Pressable onPress={() => { setCollege(null); setPreview(null); }}><Small color={colors.primary}>Change</Small></Pressable>
            </Row>
          </Card>
        ) : (
          <View>
            <Input value={query} onChangeText={setQuery} placeholder="Search e.g. COEP, PICT, VIT…" />
            <View style={styles.list}>
              {colleges.slice(0, 8).map((c) => (
                <Pressable key={c.id} onPress={() => { setCollege(c); setNameOnId(''); }} style={styles.listRow}>
                  <Text style={{ fontSize: 18 }}>{c.institution_type === 'school' ? '🏫' : '🎓'}</Text>
                  <View style={{ flex: 1 }}>
                    <Body numberOfLines={1}>{c.name}</Body>
                    <Small>{c.short_name ? `${c.short_name} · ` : ''}{c.city}</Small>
                  </View>
                </Pressable>
              ))}
              {!colleges.length ? <Small style={{ padding: spacing.md }}>No institutions match — ask us to add yours.</Small> : null}
            </View>
          </View>
        )}
        <Spacer h={spacing.lg} />

        <Input
          label="College name exactly as printed on your ID card"
          value={nameOnId}
          onChangeText={setNameOnId}
          placeholder={college ? college.name : 'Select a college first'}
          editable={!!college}
          hint="Must match the college you selected. Abbreviations like COEP / PICT are fine."
          error={preview && !preview.name_matches ? `Doesn't match ${college?.short_name || college?.name} (${Math.round(preview.name_score * 100)}% similar)` : null}
        />
        <Spacer h={spacing.lg} />
        <Input
          label="Student ID / roll number"
          value={idNumber}
          onChangeText={(t) => setIdNumber(t.toUpperCase())}
          autoCapitalize="characters"
          placeholder={college?.id_hint ?? 'e.g. 112003045'}
          editable={!!college}
          hint={preview && !preview.id_format_valid ? `Format looks unusual for ${college?.short_name || 'this college'} – you can still continue; we'll verify manually from your ID photo.` : college?.id_hint ? `Format: ${college.id_hint}` : null}
        />
        <Spacer h={spacing.lg} />

        {preview ? (
          <Card elevated={false} style={{ backgroundColor: preview.auto_verified ? colors.successLight : preview.name_matches ? colors.warningLight : colors.dangerLight, borderWidth: 0 }}>
            <Row gap={10}>
              <Text style={{ fontSize: 22 }}>{preview.auto_verified ? '✅' : preview.name_matches ? '🕒' : '⛔'}</Text>
              <View style={{ flex: 1 }}>
                <BodyBold>{preview.auto_verified ? 'Instant verification' : preview.name_matches ? 'Manual review needed' : 'College name mismatch'}</BodyBold>
                <Small>
                  {preview.auto_verified
                    ? 'Name on ID matches and the ID format is valid. You can ride right away.'
                    : preview.name_matches
                      ? 'Your ID format is unusual. Upload a photo of your ID after signing up – ops verifies within hours.'
                      : 'Type the institution name exactly as it appears on your ID card, or pick the right college.'}
                </Small>
              </View>
            </Row>
          </Card>
        ) : null}
        <Spacer h={spacing.lg} />

        <SmallBold color={colors.textSecondary} style={{ marginBottom: 6 }}>Gender</SmallBold>
        <Row gap={spacing.sm}>
          {genders.map((g) => (
            <Pressable key={g.value} onPress={() => setGender(g.value)} style={[styles.chip, gender === g.value && { backgroundColor: colors.primary, borderColor: colors.primary }]}>
              <SmallBold color={gender === g.value ? '#fff' : colors.textSecondary}>{g.label}</SmallBold>
            </Pressable>
          ))}
        </Row>
        <Spacer h={spacing.lg} />
        <Input label="Course (optional)" value={course} onChangeText={setCourse} placeholder="B.Tech Computer Engineering" />
        <Spacer h={spacing.xl} />
        {error ? <Small color={colors.danger} style={{ marginBottom: spacing.sm }}>{error}</Small> : null}
        <Button title="Create my student profile" onPress={submit} loading={loading} disabled={!canSubmit} />
        <Spacer h={spacing.md} />
        <Pressable onPress={signOut}><Small center color={colors.textMuted}>Use a different number</Small></Pressable>
      </ScrollView>
    </Screen>
  );
}

// ── Pending verification gate ──────────────────────────────────────
export function PendingVerificationScreen() {
  const user = useAuth((s) => s.user);
  const refreshUser = useAuth((s) => s.refreshUser);
  const signOut = useAuth((s) => s.signOut);
  const [uploading, setUploading] = useState(false);
  const status = user?.student?.verification_status;

  useEffect(() => {
    const t = setInterval(() => refreshUser(), 10000);
    return () => clearInterval(t);
  }, [refreshUser]);

  const pickAndUpload = async () => {
    // Lightweight picker: web uses <input type=file>; native prompts via camera roll when expo-image-picker is added.
    if (Platform.OS === 'web' && typeof document !== 'undefined') {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return;
        setUploading(true);
        try {
          const fd = new FormData();
          fd.append('file', file);
          await api.students.uploadIdCard(fd);
          toast('ID card uploaded', 'Our admin team is reviewing your details.', 'success');
          await refreshUser();
        } catch (e) {
          toast('Upload failed', e instanceof ApiError ? e.message : undefined, 'error');
        } finally {
          setUploading(false);
        }
      };
      input.click();
      return;
    }
    toast('Upload from the web app for now', 'Native camera upload arrives with the next build.');
  };

  const statusCopy = useMemo(() => {
    if (status === 'rejected') {
      return {
        emoji: '⛔',
        title: 'Verification Rejected',
        subtitle: 'Admin could not verify your college identity.',
        reason: user?.student?.verification_note || 'College ID details could not be validated. Please check the details or re-upload your ID card.',
      };
    }
    return {
      emoji: '🕒',
      title: 'Profile in Review',
      subtitle: 'Please wait for 10 minutes while admin verifies your college identity.',
      reason: user?.student?.verification_note || 'Your registration details have been submitted to the admin console for approval.',
    };
  }, [status, user?.student?.verification_note]);

  return (
    <Screen style={{ justifyContent: 'center' }}>
      <Card style={{ alignItems: 'center', gap: spacing.md, maxWidth: 440, width: '100%', alignSelf: 'center' }}>
        <Text style={{ fontSize: 52 }}>{statusCopy.emoji}</Text>
        <H2 center>{statusCopy.title}</H2>
        <Small center color={colors.textSecondary} style={{ fontWeight: '600' }}>{statusCopy.subtitle}</Small>

        {/* Informational card with review details & rejection reason if applicable */}
        <View style={{ width: '100%', backgroundColor: status === 'rejected' ? '#FEE2E2' : colors.surfaceAlt, padding: spacing.md, borderRadius: radii.md, borderWidth: 1, borderColor: status === 'rejected' ? '#FCA5A5' : colors.border }}>
          <Caption color={status === 'rejected' ? '#991B1B' : colors.textMuted}>
            {status === 'rejected' ? 'REASON FOR REJECTION' : 'STATUS NOTE'}
          </Caption>
          <SmallBold color={status === 'rejected' ? '#B91C1C' : colors.text} style={{ marginTop: 2 }}>
            {statusCopy.reason}
          </SmallBold>
        </View>

        <Row gap={8} style={{ alignItems: 'center', marginVertical: 4 }}>
          <Pill label={status ?? 'pending'} status={status ?? 'pending'} />
          <Caption>{user?.student?.college.name}</Caption>
        </Row>

        <Button title={user?.student?.id_card_url ? 'Re-upload ID card' : 'Upload ID card photo'} onPress={pickAndUpload} loading={uploading} style={{ alignSelf: 'stretch' }} />
        <Button title="Refresh Status" variant="secondary" onPress={() => refreshUser()} style={{ alignSelf: 'stretch' }} />
        <Pressable onPress={signOut} style={{ marginTop: spacing.xs }}><Small color={colors.textMuted}>Sign out / Use a different number</Small></Pressable>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  otpRow: { flexDirection: 'row', gap: 8 },
  otpCell: { flex: 1, height: 56, borderRadius: radii.md, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  list: { marginTop: 6, backgroundColor: colors.surface, borderRadius: radii.md, borderWidth: 1, borderColor: colors.border, overflow: 'hidden' },
  listRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  chip: { paddingHorizontal: 14, paddingVertical: 9, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
});
