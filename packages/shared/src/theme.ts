/**
 * Traveo design tokens — shared by the passenger app, driver app and admin panel.
 * Brand: deep indigo + electric lime accent; friendly, high-contrast, campus energy.
 */

/**
 * Traveo design tokens — shared by the passenger app, driver app and admin panel.
 * Clean Minimalist / Linear Studio aesthetic: crisp slate neutrals, refined indigo/emerald accents,
 * high-contrast typography, precision borders and layered elevation.
 */

export const colors = {
  primary: '#3B82F6', // Sleek Linear electric blue
  primaryDark: '#1D4ED8',
  primaryLight: '#EFF6FF',
  accent: '#10B981', // Crisp emerald accent
  accentDark: '#047857',
  success: '#10B981',
  successLight: '#ECFDF5',
  warning: '#F59E0B',
  warningLight: '#FFFBEB',
  danger: '#EF4444',
  dangerLight: '#FEF2F2',
  info: '#0284C7',
  infoLight: '#F0F9FF',

  text: '#090D16', // Ultra crisp deep ink
  textSecondary: '#4B5563',
  textMuted: '#9CA3AF',
  textInverse: '#FFFFFF',

  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceAlt: '#F1F5F9',
  border: '#E2E8F0',
  borderStrong: '#CBD5E1',
  overlay: 'rgba(9, 13, 22, 0.65)',

  driver: '#0284C7',
  rider: '#6366F1',
  campus: '#3B82F6',
  pickup: '#10B981',
  drop: '#EF4444',
  route: '#3B82F6',
} as const;

export const spacing = { xxs: 2, xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 28, xxxl: 36 } as const;

export const radii = { sm: 6, md: 10, lg: 14, xl: 20, pill: 999 } as const;

export const typography = {
  display: { fontSize: 32, fontWeight: '800' as const, lineHeight: 38, letterSpacing: -0.6 },
  h1: { fontSize: 24, fontWeight: '750' as const, lineHeight: 30, letterSpacing: -0.5 },
  h2: { fontSize: 19, fontWeight: '700' as const, lineHeight: 25, letterSpacing: -0.3 },
  h3: { fontSize: 16, fontWeight: '650' as const, lineHeight: 22, letterSpacing: -0.2 },
  body: { fontSize: 14, fontWeight: '400' as const, lineHeight: 21, letterSpacing: -0.1 },
  bodyBold: { fontSize: 14, fontWeight: '600' as const, lineHeight: 21, letterSpacing: -0.1 },
  small: { fontSize: 13, fontWeight: '400' as const, lineHeight: 18 },
  smallBold: { fontSize: 13, fontWeight: '600' as const, lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: '600' as const, lineHeight: 14, letterSpacing: 0.5 },
  mono: { fontSize: 28, fontWeight: '800' as const, letterSpacing: 6 },
} as const;

export const shadows = {
  card: {
    shadowColor: '#090D16',
    shadowOpacity: 0.05,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  float: {
    shadowColor: '#090D16',
    shadowOpacity: 0.12,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
} as const;

export const statusColors: Record<string, { bg: string; fg: string }> = {
  open: { bg: '#F0F9FF', fg: '#0284C7' },
  locked: { bg: '#FFFBEB', fg: '#D97706' },
  driver_assigned: { bg: '#EFF6FF', fg: '#1D4ED8' },
  in_progress: { bg: '#ECFDF5', fg: '#059669' },
  completed: { bg: '#F1F5F9', fg: '#475569' },
  no_driver: { bg: '#FEF2F2', fg: '#DC2626' },
  cancelled: { bg: '#FEF2F2', fg: '#DC2626' },
  expired: { bg: '#F1F5F9', fg: '#94A3B8' },
  verified: { bg: '#ECFDF5', fg: '#059669' },
  pending: { bg: '#FFFBEB', fg: '#D97706' },
  rejected: { bg: '#FEF2F2', fg: '#DC2626' },
  online: { bg: '#ECFDF5', fg: '#059669' },
  offline: { bg: '#F1F5F9', fg: '#64748B' },
  on_trip: { bg: '#EFF6FF', fg: '#1D4ED8' },
};
