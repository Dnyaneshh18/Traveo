import React from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type PressableProps,
  type StyleProp,
  type TextInputProps,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, radii, shadows, spacing, statusColors, typography, initials } from '@traveo/shared';
import { useUiStore } from './toast';

// ── Screen ─────────────────────────────────────────────────────────
export function Screen({
  children,
  style,
  padded = true,
  edges,
  maxWidth = 480,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  padded?: boolean;
  edges?: ('top' | 'bottom' | 'left' | 'right')[];
  maxWidth?: number;
}) {
  return (
    <SafeAreaView edges={edges ?? ['top', 'left', 'right']} style={styles.screenRoot}>
      <View
        style={[
          styles.screenContainer,
          padded && { paddingHorizontal: spacing.lg },
          maxWidth ? { maxWidth } : null,
          style,
        ]}
      >
        {children}
      </View>
    </SafeAreaView>
  );
}

// ── Typography ─────────────────────────────────────────────────────
type TProps = { children: React.ReactNode; style?: StyleProp<TextStyle>; color?: string; center?: boolean; numberOfLines?: number };
const mk = (base: TextStyle, defaultColor: string = colors.text) =>
  function T({ children, style, color, center, numberOfLines }: TProps) {
    return (
      <Text numberOfLines={numberOfLines} style={[base, { color: color ?? defaultColor }, center && { textAlign: 'center' }, style]}>
        {children}
      </Text>
    );
  };
export const Display = mk(typography.display);
export const H1 = mk(typography.h1);
export const H2 = mk(typography.h2);
export const H3 = mk(typography.h3);
export const Body = mk(typography.body);
export const BodyBold = mk(typography.bodyBold);
export const Small = mk(typography.small, colors.textSecondary);
export const SmallBold = mk(typography.smallBold, colors.textSecondary);
export const Caption = mk({ ...typography.caption, textTransform: 'uppercase' }, colors.textMuted);

// ── Button ─────────────────────────────────────────────────────────
type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent';
export function Button({
  title,
  onPress,
  variant = 'primary',
  loading,
  disabled,
  icon,
  style,
  size = 'lg',
  ...rest
}: { title: string; variant?: Variant; loading?: boolean; icon?: React.ReactNode; size?: 'md' | 'lg'; style?: StyleProp<ViewStyle> } & PressableProps) {
  const bg: Record<Variant, string> = {
    primary: colors.primary,
    secondary: colors.surfaceAlt,
    ghost: 'transparent',
    danger: colors.dangerLight,
    accent: colors.accent,
  };
  const fg: Record<Variant, string> = {
    primary: '#fff',
    secondary: colors.text,
    ghost: colors.text,
    danger: colors.danger,
    accent: '#fff',
  };
  const isDisabled = disabled || loading;
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.button,
        size === 'md' && { paddingVertical: 10, paddingHorizontal: 14, borderRadius: radii.md },
        { backgroundColor: bg[variant], opacity: isDisabled ? 0.45 : pressed ? 0.88 : 1 },
        variant === 'ghost' && { borderWidth: 1, borderColor: colors.border },
        variant === 'secondary' && { borderWidth: 1, borderColor: colors.border },
        variant === 'primary' && {
          shadowColor: colors.primary,
          shadowOpacity: 0.25,
          shadowRadius: 10,
          shadowOffset: { width: 0, height: 4 },
        },
        Platform.OS === 'web' && ({ cursor: isDisabled ? 'not-allowed' : 'pointer', transition: 'all 0.15s ease' } as any),
        style,
      ]}
      {...rest}
    >
      {loading ? <ActivityIndicator color={fg[variant]} /> : (
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          {icon}
          <Text style={[size === 'md' ? typography.smallBold : typography.bodyBold, { color: fg[variant] }]}>{title}</Text>
        </View>
      )}
    </Pressable>
  );
}

// ── Card ───────────────────────────────────────────────────────────
export function Card({ children, style, onPress, elevated = true }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; onPress?: () => void; elevated?: boolean }) {
  const content = <View style={[styles.card, elevated && shadows.card, style]}>{children}</View>;
  if (!onPress) return content;
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        { opacity: pressed ? 0.94 : 1, transform: [{ scale: pressed ? 0.995 : 1 }] },
        Platform.OS === 'web' && ({ cursor: 'pointer', transition: 'all 0.15s ease' } as any),
      ]}
    >
      {content}
    </Pressable>
  );
}

// ── Input ──────────────────────────────────────────────────────────
export function Input({
  label,
  error,
  hint,
  style,
  right,
  ...rest
}: { label?: string; error?: string | null; hint?: string | null; right?: React.ReactNode } & TextInputProps) {
  const [focused, setFocused] = React.useState(false);
  return (
    <View style={{ gap: 6 }}>
      {label ? <SmallBold color={colors.textSecondary}>{label}</SmallBold> : null}
      <View
        style={[
          styles.inputWrap,
          focused ? { borderColor: colors.primary, backgroundColor: '#FFFFFF', ...shadows.card } : null,
          error ? { borderColor: colors.danger } : null,
        ]}
      >
        <TextInput
          placeholderTextColor={colors.textMuted}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={[styles.input, Platform.OS === 'web' && ({ outlineStyle: 'none' } as any), style]}
          {...rest}
        />
        {right}
      </View>
      {error ? <Small color={colors.danger}>{error}</Small> : hint ? <Small>{hint}</Small> : null}
    </View>
  );
}

// ── Pill ───────────────────────────────────────────────────────────
export function Pill({ label, status, color, bg, style }: { label: string; status?: string; color?: string; bg?: string; style?: StyleProp<ViewStyle> }) {
  const sc = status ? statusColors[status] : undefined;
  return (
    <View style={[styles.pill, { backgroundColor: bg ?? sc?.bg ?? colors.surfaceAlt }, style]}>
      <Text style={[typography.caption, { color: color ?? sc?.fg ?? colors.textSecondary, textTransform: 'uppercase' }]}>{label}</Text>
    </View>
  );
}

// ── Avatar ─────────────────────────────────────────────────────────
export function Avatar({ name, size = 40, color = colors.primary, ring }: { name: string; size?: number; color?: string; ring?: string }) {
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: color, alignItems: 'center', justifyContent: 'center', borderWidth: ring ? 2 : 0, borderColor: ring }}>
      <Text style={{ color: '#fff', fontWeight: '700', fontSize: size * 0.38 }}>{initials(name) || '?'}</Text>
    </View>
  );
}

// ── Row / Divider / Spacer ─────────────────────────────────────────
export const Row = ({ children, style, gap = spacing.sm, between }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; gap?: number; between?: boolean }) => (
  <View style={[{ flexDirection: 'row', alignItems: 'center', gap }, between && { justifyContent: 'space-between' }, style]}>{children}</View>
);
export const Divider = ({ style }: { style?: StyleProp<ViewStyle> }) => <View style={[{ height: StyleSheet.hairlineWidth, backgroundColor: colors.border, marginVertical: spacing.md }, style]} />;
export const Spacer = ({ h = spacing.md }: { h?: number }) => <View style={{ height: h }} />;

// ── Empty / Loading ────────────────────────────────────────────────
export function Empty({ emoji = '🛺', title, body, action }: { emoji?: string; title: string; body?: string; action?: React.ReactNode }) {
  return (
    <View style={{ alignItems: 'center', paddingVertical: spacing.xxxl, paddingHorizontal: spacing.xl, gap: spacing.sm }}>
      <Text style={{ fontSize: 44 }}>{emoji}</Text>
      <H3 center>{title}</H3>
      {body ? <Small center>{body}</Small> : null}
      {action ? <View style={{ marginTop: spacing.md }}>{action}</View> : null}
    </View>
  );
}
export const Loading = ({ label }: { label?: string }) => (
  <View style={{ alignItems: 'center', justifyContent: 'center', padding: spacing.xxl, gap: spacing.sm }}>
    <ActivityIndicator color={colors.primary} />
    {label ? <Small>{label}</Small> : null}
  </View>
);

// ── Toasts ─────────────────────────────────────────────────────────
export function ToastHost() {
  const toasts = useUiStore((s) => s.toasts);
  const dismiss = useUiStore((s) => s.dismiss);
  if (!toasts.length) return null;
  const tone = { info: colors.text, success: colors.success, error: colors.danger };
  return (
    <View pointerEvents="box-none" style={styles.toastHost}>
      {toasts.map((t) => (
        <View
          key={t.id}
          style={[styles.toast, { borderLeftColor: tone[t.kind] }]}
        >
          <View style={{ flex: 1 }}>
            <BodyBold color="#fff">{t.title}</BodyBold>
            {t.body ? <Small color="#CBD5E1">{t.body}</Small> : null}
          </View>
          {t.action ? (
            <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
              <Pressable
                onPress={() => {
                  t.action?.onPress();
                  dismiss(t.id);
                }}
                style={({ pressed }) => [
                  styles.toastActionBtn,
                  { backgroundColor: colors.success, opacity: pressed ? 0.8 : 1 },
                  Platform.OS === 'web' && ({ cursor: 'pointer' } as any),
                ]}
              >
                <Text style={{ color: '#fff', fontWeight: '700', fontSize: 13 }}>{t.action.label}</Text>
              </Pressable>
              <Pressable
                onPress={() => dismiss(t.id)}
                style={({ pressed }) => [
                  styles.toastActionBtn,
                  { backgroundColor: 'rgba(255,255,255,0.15)', opacity: pressed ? 0.8 : 1 },
                  Platform.OS === 'web' && ({ cursor: 'pointer' } as any),
                ]}
              >
                <Text style={{ color: '#fff', fontWeight: '600', fontSize: 13 }}>Dismiss</Text>
              </Pressable>
            </View>
          ) : null}
        </View>
      ))}
    </View>
  );
}

// ── Connection dot ─────────────────────────────────────────────────
export function ConnectionDot() {
  const state = useUiStore((s) => s.connection);
  const c = state === 'open' ? colors.success : state === 'connecting' ? colors.warning : colors.textMuted;
  return <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: c }} />;
}

// ── Stepper / Segmented ────────────────────────────────────────────
export function Segmented<T extends string>({ options, value, onChange }: { options: { value: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  return (
    <View style={styles.segmented}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable
            key={o.value}
            onPress={() => onChange(o.value)}
            style={[
              styles.segment,
              active && { backgroundColor: '#FFFFFF', ...shadows.card },
              Platform.OS === 'web' && ({ cursor: 'pointer', transition: 'all 0.15s ease' } as any),
            ]}
          >
            <Text style={[typography.smallBold, { color: active ? colors.text : colors.textSecondary }]}>{o.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function Stepper({ value, min = 1, max = 4, onChange }: { value: number; min?: number; max?: number; onChange: (v: number) => void }) {
  return (
    <Row gap={spacing.md}>
      <Pressable onPress={() => onChange(Math.max(min, value - 1))} style={styles.stepBtn}><Text style={styles.stepTxt}>−</Text></Pressable>
      <H3>{value}</H3>
      <Pressable onPress={() => onChange(Math.min(max, value + 1))} style={styles.stepBtn}><Text style={styles.stepTxt}>+</Text></Pressable>
    </Row>
  );
}

const styles = StyleSheet.create({
  screenRoot: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    alignItems: 'center', // Centers content on wide web browsers
    width: '100%',
  },
  screenContainer: {
    flex: 1,
    width: '100%',
    alignSelf: 'center',
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radii.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: radii.md,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
  },
  input: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 14,
    color: colors.text,
  },
  pill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.sm,
    alignSelf: 'flex-start',
  },
  toastHost: {
    position: 'absolute',
    top: 54,
    left: 16,
    right: 16,
    maxWidth: 440,
    alignSelf: 'center',
    gap: 8,
    zIndex: 999,
  },
  toast: {
    backgroundColor: '#090D16',
    borderRadius: radii.md,
    padding: 14,
    borderLeftWidth: 4,
    ...shadows.float,
  },
  toastActionBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmented: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: radii.md,
    padding: 3,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  segment: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: radii.sm,
  },
  stepBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#DBEAFE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepTxt: {
    color: '#1D4ED8',
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 20,
  },
});
