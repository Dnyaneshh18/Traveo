/**
 * Traveo design tokens — shared by the passenger app, driver app and admin panel.
 * Brand: deep indigo + electric lime accent; friendly, high-contrast, campus energy.
 */

export const colors = {
  primary: '#4F46E5',
  primaryDark: '#3730A3',
  primaryLight: '#EEF2FF',
  accent: '#A3E635',
  accentDark: '#65A30D',
  success: '#16A34A',
  successLight: '#DCFCE7',
  warning: '#F59E0B',
  warningLight: '#FEF3C7',
  danger: '#DC2626',
  dangerLight: '#FEE2E2',
  info: '#0EA5E9',
  infoLight: '#E0F2FE',

  text: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',
  textInverse: '#FFFFFF',

  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceAlt: '#F1F5F9',
  border: '#E2E8F0',
  borderStrong: '#CBD5E1',
  overlay: 'rgba(15, 23, 42, 0.55)',

  driver: '#0EA5E9',
  rider: '#8B5CF6',
  campus: '#4F46E5',
  pickup: '#16A34A',
  drop: '#DC2626',
  route: '#4F46E5',
} as const;

export const spacing = { xxs: 2, xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 28, xxxl: 36 } as const;

export const radii = { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 } as const;

export const typography = {
  display: { fontSize: 32, fontWeight: '800' as const, lineHeight: 38 },
  h1: { fontSize: 26, fontWeight: '800' as const, lineHeight: 32 },
  h2: { fontSize: 20, fontWeight: '700' as const, lineHeight: 26 },
  h3: { fontSize: 17, fontWeight: '700' as const, lineHeight: 22 },
  body: { fontSize: 15, fontWeight: '400' as const, lineHeight: 21 },
  bodyBold: { fontSize: 15, fontWeight: '600' as const, lineHeight: 21 },
  small: { fontSize: 13, fontWeight: '400' as const, lineHeight: 18 },
  smallBold: { fontSize: 13, fontWeight: '600' as const, lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: '500' as const, lineHeight: 14, letterSpacing: 0.4 },
  mono: { fontSize: 28, fontWeight: '800' as const, letterSpacing: 6 },
} as const;

export const shadows = {
  card: {
    shadowColor: '#0F172A',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  float: {
    shadowColor: '#0F172A',
    shadowOpacity: 0.16,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
} as const;

export const statusColors: Record<string, { bg: string; fg: string }> = {
  open: { bg: colors.infoLight, fg: '#0369A1' },
  locked: { bg: colors.warningLight, fg: '#B45309' },
  driver_assigned: { bg: colors.primaryLight, fg: colors.primaryDark },
  in_progress: { bg: colors.successLight, fg: '#15803D' },
  completed: { bg: colors.surfaceAlt, fg: colors.textSecondary },
  no_driver: { bg: colors.dangerLight, fg: '#B91C1C' },
  cancelled: { bg: colors.dangerLight, fg: '#B91C1C' },
  expired: { bg: colors.surfaceAlt, fg: colors.textMuted },
  verified: { bg: colors.successLight, fg: '#15803D' },
  pending: { bg: colors.warningLight, fg: '#B45309' },
  rejected: { bg: colors.dangerLight, fg: '#B91C1C' },
  online: { bg: colors.successLight, fg: '#15803D' },
  offline: { bg: colors.surfaceAlt, fg: colors.textSecondary },
  on_trip: { bg: colors.primaryLight, fg: colors.primaryDark },
};
