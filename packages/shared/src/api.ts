/**
 * Traveo API client — framework agnostic (React Native + web).
 *
 * • Standard envelope unwrapping ({success, data, message})
 * • Automatic access-token refresh on 401 (single-flight)
 * • Typed helpers for every endpoint used by the apps
 */

import type {
  ApiEnvelope,
  ApiErrorBody,
  AppNotification,
  AuthResult,
  College,
  DriverEarnings,
  DriverOffer,
  FeedItem,
  Place,
  PlaceSuggestion,
  RideRequest,
  RoutePreview,
  TimelineEvent,
  TokenPair,
  TripView,
  User,
  UserRole,
  VehicleType,
} from './types';

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;
  requestId?: string;

  constructor(status: number, code: string, message: string, details?: unknown, requestId?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

export interface TokenStorage {
  get(): Promise<TokenPair | null> | TokenPair | null;
  set(tokens: TokenPair | null): Promise<void> | void;
}

export interface ApiClientOptions {
  baseUrl: string; // e.g. http://192.168.1.5:8000
  prefix?: string; // default /api/v1
  tokens: TokenStorage;
  onUnauthorized?: () => void;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

type Query = Record<string, string | number | boolean | null | undefined>;

export function createApiClient(opts: ApiClientOptions) {
  const prefix = opts.prefix ?? '/api/v1';
  const base = opts.baseUrl.replace(/\/+$/, '');
  // Wrap the global fetch – calling an unbound reference throws "Illegal invocation" in browsers.
  const fetchImpl: typeof fetch = opts.fetchImpl ?? ((input, init) => fetch(input, init));
  let refreshing: Promise<TokenPair | null> | null = null;

  const buildUrl = (path: string, query?: Query, token?: string | null) => {
    const url = `${base}${path.startsWith('/api') ? '' : prefix}${path}`;
    const queryParams: Record<string, string | number | boolean | null | undefined> = { ...(query || {}) };
    if (token && !queryParams._token) {
      queryParams._token = token;
    }
    const qs = Object.entries(queryParams)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join('&');
    return qs ? `${url}?${qs}` : url;
  };

  async function refreshTokens(): Promise<TokenPair | null> {
    if (!refreshing) {
      refreshing = (async () => {
        const current = await opts.tokens.get();
        if (!current?.refresh_token) return null;
        try {
          const res = await fetchImpl(buildUrl('/auth/refresh'), {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ refresh_token: current.refresh_token }),
          });
          if (!res.ok) {
            console.warn('[ApiClient] refresh failed with status:', res.status);
            return null;
          }
          const body = (await res.json()) as ApiEnvelope<TokenPair>;
          console.log('[ApiClient] refresh success! Setting new tokens into tokenStore');
          await opts.tokens.set(body.data);
          return body.data;
        } catch (e) {
          console.warn('[ApiClient] refresh exception:', e);
          return null;
        } finally {
          setTimeout(() => (refreshing = null), 0);
        }
      })();
    }
    return refreshing;
  }

  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    query?: Query,
    options: { auth?: boolean; retry?: boolean; formData?: FormData } = {},
  ): Promise<ApiEnvelope<T>> {
    const auth = options.auth ?? true;
    const headers: Record<string, string> = {
      accept: 'application/json',
      Authorization: '',
    };
    if (body !== undefined && !options.formData) headers['content-type'] = 'application/json';
    let tokens: TokenPair | null = null;
    if (auth) {
      tokens = await opts.tokens.get();
      if (!tokens?.access_token && tokens?.refresh_token) {
        tokens = await refreshTokens();
      }
      if (tokens?.access_token) {
        headers['Authorization'] = `Bearer ${tokens.access_token}`;
        headers['authorization'] = `Bearer ${tokens.access_token}`;
      } else {
        console.warn('[ApiClient] auth requested but no token available for path:', path, 'tokens:', tokens);
      }
    }
    const controller = typeof AbortController !== 'undefined' ? new AbortController() : undefined;
    const timer = controller ? setTimeout(() => controller.abort(), opts.timeoutMs ?? 20000) : undefined;
    let res: Response;
    try {
      // Remove empty Authorization header if not set
      if (!headers.Authorization) delete headers.Authorization;
      if (!headers.authorization) delete headers.authorization;
      const activeToken = tokens?.access_token || null;
      res = await fetchImpl(buildUrl(path, query, activeToken), {
        method,
        headers,
        credentials: 'same-origin',
        body: options.formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
        signal: controller?.signal,
      });
    } catch (e: any) {
      if (timer) clearTimeout(timer);
      throw new ApiError(0, 'network_error', e?.name === 'AbortError' ? 'Request timed out' : 'Cannot reach the Traveo server');
    }
    if (timer) clearTimeout(timer);

    if (res.status === 401 && auth && options.retry !== false) {
      const refreshed = await refreshTokens();
      if (refreshed?.access_token) {
        return request<T>(method, path, body, query, { ...options, retry: false });
      }
      console.warn('[ApiClient] 401 received and refresh returned null for path:', path);
    }

    const text = await res.text();
    let json: any = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch {
      json = null;
    }
    if (!res.ok) {
      const err = json as ApiErrorBody | null;
      throw new ApiError(
        res.status,
        err?.error?.code ?? `http_${res.status}`,
        err?.error?.message ?? res.statusText ?? 'Request failed',
        err?.error?.details,
        err?.request_id,
      );
    }
    return json as ApiEnvelope<T>;
  }

  const get = <T,>(path: string, query?: Query, auth = true) => request<T>('GET', path, undefined, query, { auth });
  const post = <T,>(path: string, body?: unknown, auth = true) => request<T>('POST', path, body, undefined, { auth });
  const put = <T,>(path: string, body?: unknown) => request<T>('PUT', path, body);
  const del = <T,>(path: string) => request<T>('DELETE', path);

  return {
    request,
    baseUrl: base,
    wsUrl(token: string) {
      const wsBase = base.replace(/^http/, 'ws');
      return `${wsBase}/ws?token=${encodeURIComponent(token)}`;
    },

    auth: {
      requestOtp: (phone: string, role: UserRole) =>
        post<{ phone: string; expires_in_seconds: number; dev_otp?: string | null }>('/auth/otp/request', { phone, role }, false),
      verifyOtp: (phone: string, otp: string, role: UserRole, push_token?: string | null) =>
        post<AuthResult>('/auth/otp/verify', { phone, otp, role, push_token }, false),
      adminLogin: (email: string, password: string) => post<AuthResult>('/auth/admin/login', { email, password }, false),
      me: () => get<User>('/auth/me'),
      logout: (refresh_token?: string | null) => post<null>('/auth/logout', refresh_token ? { refresh_token } : undefined),
      setPushToken: (push_token: string) => put<null>('/me/push-token'.replace('/me', '/auth/me'), { push_token }),
    },

    colleges: {
      search: (q?: string, city?: string) => get<College[]>('/colleges', { q, city }, false),
      get: (id: string) => get<College>(`/colleges/${id}`, undefined, false),
    },

    students: {
      identityPreview: (body: { college_id: string; college_name_on_id: string; college_id_number: string }) =>
        post<{ name_matches: boolean; name_score: number; id_format_valid: boolean; auto_verified: boolean; id_hint?: string | null }>(
          '/students/identity/preview',
          body,
          false // public preview helper: doesn't need auth token
        ),
      register: (body: {
        full_name: string;
        college_id: string;
        college_name_on_id: string;
        college_id_number: string;
        gender?: string | null;
        course?: string | null;
        graduation_year?: number | null;
        emergency_contact?: string | null;
      }) => post<User>('/students/register', body),
      update: (body: Record<string, unknown>) => put<User>('/students/me', body),
      uploadIdCard: (formData: FormData) => request<{ id_card_url: string }>('POST', '/students/me/id-card', undefined, undefined, { formData }),
      stats: () => get<{ completed_rides: number; cancelled_rides: number; total_saved_inr: number; average_rating: number; rating_count: number; co2_saved_kg: number }>('/students/me/stats'),
    },

    rides: {
      preview: (origin: Place, destination: Place) => post<RoutePreview>('/rides/preview', { origin, destination }, false),
      create: (body: {
        origin: Place;
        destination: Place;
        vehicle_type: VehicleType;
        seats?: number;
        departure_at?: string | null;
        note?: string | null;
        women_only?: boolean;
      }) => post<RideRequest>('/rides/requests', body),
      feed: (query: { pickup_lat?: number; pickup_lng?: number; drop_lat?: number; drop_lng?: number; departure_at?: string; vehicle_type?: VehicleType }) =>
        get<FeedItem[]>('/rides/feed', query),
      active: () => get<RideRequest | null>('/rides/active'),
      history: (limit = 20, offset = 0) => get<RideRequest[]>('/rides/history', { limit, offset }),
      detail: (id: string) => get<RideRequest>(`/rides/requests/${id}`),
      timeline: (id: string) => get<TimelineEvent[]>(`/rides/requests/${id}/timeline`),
      join: (id: string, body: { pickup: Place; drop: Place; seats?: number }) => post<RideRequest>(`/rides/requests/${id}/join`, body),
      leave: (id: string) => post<RideRequest | null>(`/rides/requests/${id}/leave`),
      hide: (id: string) => post<null>(`/rides/requests/${id}/hide`),
      removeMember: (id: string, userId: string) => del<RideRequest>(`/rides/requests/${id}/members/${userId}`),
      lock: (id: string) => post<RideRequest>(`/rides/requests/${id}/lock`),
      retry: (id: string) => post<RideRequest>(`/rides/requests/${id}/retry`),
      reopen: (id: string) => post<RideRequest>(`/rides/requests/${id}/reopen`),
      cancel: (id: string, reason?: string) => post<null>(`/rides/requests/${id}/cancel`, reason ? { reason } : undefined),
      payments: (rideId: string) => get<Array<{ id: string; payer_id: string; amount_inr: number; method: string; status: string; paid_at?: string | null }>>(`/rides/${rideId}/payments`),
      confirmPayment: (rideId: string, method: string, reference?: string) => post<{ status: string }>(`/rides/${rideId}/payments/confirm`, { method, reference }),
      rate: (body: { ride_id: string; ratee_id?: string; stars: number; comment?: string }) => post<null>('/ratings', body),
      pendingRating: () => get<{
        ride_id: string;
        request_id: string;
        role: 'passenger' | 'driver';
        driver_name?: string;
        driver_id?: string;
        passenger_count?: number;
        origin_address?: string;
        destination_address?: string;
        fare_share_inr?: number;
        completed_at?: string | null;
      } | null>('/ratings/pending'),
    },

    drivers: {
      register: (body: { full_name: string; license_number: string; vehicle_type: VehicleType; registration_number: string; make_model?: string; color?: string }) =>
        post<User>('/drivers/register', body),
      setStatus: (online: boolean, lat?: number, lng?: number) => put<{ status: string }>('/drivers/me/status', { online, lat, lng }),
      location: (body: { lat: number; lng: number; heading?: number | null; speed?: number | null; accuracy?: number | null }) => post<null>('/drivers/me/location', body),
      offer: () => get<DriverOffer | null>('/drivers/me/offer'),
      accept: (offerId: string) => post<TripView>(`/drivers/offers/${offerId}/accept`),
      reject: (offerId: string, reason?: string) => post<null>(`/drivers/offers/${offerId}/reject`, reason ? { reason } : undefined),
      trip: () => get<TripView | null>('/drivers/me/trip'),
      arrived: (rideId: string) => post<TripView>(`/drivers/trips/${rideId}/arrived`),
      verify: (rideId: string, code: string) => post<TripView>(`/drivers/trips/${rideId}/verify`, { code }),
      noShow: (rideId: string, memberId: string) => post<TripView>(`/drivers/trips/${rideId}/no-show`, { member_id: memberId }),
      drop: (rideId: string, memberId: string) => post<TripView>(`/drivers/trips/${rideId}/drop`, { member_id: memberId }),
      cancel: (rideId: string, reason: string) => post<null>(`/drivers/trips/${rideId}/cancel`, { reason }),
      earnings: () => get<DriverEarnings>('/drivers/me/earnings'),
      history: (limit = 20, offset = 0) => get<any[]>('/drivers/me/history', { limit, offset }),
    },

    maps: {
      autosuggest: (q: string, near?: { lat: number; lng: number } | null) => get<PlaceSuggestion[]>('/maps/autosuggest', { q, lat: near?.lat, lng: near?.lng }, false),
      reverseGeocode: (lat: number, lng: number) => get<{ lat: number; lng: number; address: string }>('/maps/reverse-geocode', { lat, lng }, false),
      route: (waypoints: { lat: number; lng: number }[]) => post<{ distance_km: number; duration_min: number; polyline: string; legs: any[]; provider: string } | null>('/maps/route', { waypoints }, false),
      config: () => get<{ provider: string; default_center: { lat: number; lng: number }; default_zoom: number; attribution: string }>('/maps/config', undefined, false),
    },

    notifications: {
      list: (limit = 30) => get<AppNotification[]>('/notifications', { limit }),
      readAll: () => post<null>('/notifications/read'),
      read: (id: string) => post<null>(`/notifications/${id}/read`),
    },

    admin: {
      dashboard: () => get<any>('/admin/dashboard'),
      live: () => get<any>('/admin/live'),
      students: (query: Query) => get<any[]>('/admin/students', query),
      verifyStudent: (profileId: string, status: string, note?: string) => post<null>(`/admin/students/${profileId}/verify`, { status, note }),
      drivers: (query: Query) => get<any[]>('/admin/drivers', query),
      verifyDriver: (profileId: string, status: string, note?: string) => post<null>(`/admin/drivers/${profileId}/verify`, { status, note }),
      toggleUser: (userId: string, is_active: boolean) => post<null>(`/admin/users/${userId}/active`, { is_active }),
      rides: (query: Query) => get<RideRequest[]>('/admin/rides', query),
      ride: (id: string) => get<any>(`/admin/rides/${id}`),
      cancelRide: (id: string) => post<null>(`/admin/rides/${id}/cancel`),
      config: () => get<Array<{ key: string; value: any; default: any; description: string }>>('/admin/config'),
      setConfig: (key: string, value: unknown) => put<null>('/admin/config', { key, value }),
      colleges: () => get<College[]>('/colleges', { limit: 100 }, false),
      createCollege: (body: Record<string, unknown>) => post<College>('/colleges', body),
      updateCollege: (id: string, body: Record<string, unknown>) => put<College>(`/colleges/${id}`, body),
    },
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
