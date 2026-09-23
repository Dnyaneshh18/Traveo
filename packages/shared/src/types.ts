/**
 * Traveo — shared domain types (mirrors backend/app/models/enums.py + schemas).
 */

export type UserRole = 'student' | 'driver' | 'admin';
export type InstitutionType = 'college' | 'school';
export type VerificationStatus = 'pending' | 'verified' | 'rejected';
export type Gender = 'male' | 'female' | 'other';
export type VehicleType = 'bike' | 'auto' | 'car' | 'car_xl';
export type RideDirection = 'from_college' | 'to_college';
export type RideRequestStatus =
  | 'open'
  | 'locked'
  | 'driver_assigned'
  | 'in_progress'
  | 'completed'
  | 'no_driver'
  | 'cancelled'
  | 'expired';
export type MemberRole = 'creator' | 'member';
export type MemberStatus = 'accepted' | 'left' | 'removed' | 'picked_up' | 'dropped' | 'no_show';
export type DriverStatus = 'offline' | 'online' | 'on_trip';
export type RideStatus = 'driver_assigned' | 'in_progress' | 'completed' | 'cancelled';
export type PaymentMethod = 'cash' | 'upi' | 'wallet';
export type NotificationType = 'group' | 'ride' | 'driver' | 'system';

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Place extends LatLng {
  address: string;
  name?: string | null;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message?: string | null;
  meta?: Record<string, unknown> | null;
}

export interface ApiErrorBody {
  success: false;
  error: { code: string; message: string; details?: unknown };
  request_id?: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface CollegeBrief {
  id: string;
  code: string;
  name: string;
  short_name?: string | null;
  city: string;
  latitude: number;
  longitude: number;
  institution_type: InstitutionType | string;
  address?: string | null;
}

export interface College extends CollegeBrief {
  aliases: string[];
  state?: string | null;
  id_hint?: string | null;
  id_pattern?: string | null;
  is_active: boolean;
}

export interface StudentProfile {
  college: CollegeBrief;
  college_id_number: string;
  college_name_on_id: string;
  identity_match_score: number;
  verification_status: VerificationStatus;
  verification_note?: string | null;
  id_card_url?: string | null;
  gender?: Gender | null;
  course?: string | null;
  graduation_year?: number | null;
  emergency_contact?: string | null;
  average_rating: number;
  rating_count: number;
  completed_rides: number;
  total_saved_inr: number;
}

export interface Vehicle {
  id: string;
  vehicle_type: VehicleType;
  registration_number: string;
  make_model?: string | null;
  color?: string | null;
  seat_capacity: number;
  is_verified: boolean;
}

export interface DriverProfile {
  license_number?: string | null;
  verification_status: VerificationStatus;
  verification_note?: string | null;
  status: DriverStatus;
  average_rating: number;
  rating_count: number;
  completed_rides: number;
  total_earnings_inr: number;
  acceptance_rate: number;
  current_ride_id?: string | null;
  vehicle?: Vehicle | null;
}

export interface User {
  id: string;
  phone?: string | null;
  email?: string | null;
  role: UserRole;
  full_name: string;
  avatar_url?: string | null;
  profile_completed: boolean;
  student?: StudentProfile | null;
  driver?: DriverProfile | null;
}

export interface AuthResult {
  tokens: TokenPair;
  user: User;
  is_new_user: boolean;
}

export interface FareOption {
  vehicle_type: VehicleType;
  label: string;
  seat_capacity: number;
  total_estimate: number;
  per_seat_if_full: number;
  solo_estimate: number;
}

export interface RoutePreview {
  distance_km: number;
  duration_min: number;
  polyline: string;
  provider: string;
  direction: RideDirection;
  options: FareOption[];
}

export interface RideMember {
  id: string;
  user_id: string;
  full_name: string;
  avatar_url?: string | null;
  gender?: Gender | null;
  course?: string | null;
  rating: number;
  role: MemberRole;
  status: MemberStatus;
  seats: number;
  pickup_lat: number;
  pickup_lng: number;
  pickup_address: string;
  drop_lat: number;
  drop_lng: number;
  drop_address: string;
  pickup_order?: number | null;
  drop_order?: number | null;
  pickup_eta_min?: number | null;
  distance_km?: number | null;
  fare_share_inr?: number | null;
  detour_km: number;
  match_score: number;
  joined_at: string;
  picked_up_at?: string | null;
  dropped_at?: string | null;
  is_me: boolean;
}

export interface LivePosition {
  user_id: string;
  role: 'driver' | 'student' | string;
  lat: number;
  lng: number;
  heading?: number | null;
  speed?: number | null;
  accuracy?: number | null;
  ride_id?: string | null;
  updated_at?: number | null;
}

export interface RideDriver {
  user_id: string;
  full_name: string;
  avatar_url?: string | null;
  phone?: string | null;
  rating: number;
  completed_rides: number;
  vehicle_type: VehicleType;
  vehicle_label: string;
  registration_number?: string | null;
  make_model?: string | null;
  color?: string | null;
  eta_min?: number | null;
  position?: Partial<LivePosition> | null;
}

export interface RideInfo {
  id: string;
  status: RideStatus;
  otp_verified_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  total_fare_inr?: number | null;
  total_distance_km?: number | null;
}

export interface DispatchInfo {
  started_at?: string | null;
  radius_km?: number | null;
  attempts: number;
  max_radius_km: number;
}

export interface RideRequest {
  id: string;
  creator_id: string;
  college_id: string;
  college_name: string;
  direction: RideDirection;
  vehicle_type: VehicleType;
  vehicle_label: string;
  seat_capacity: number;
  seats_taken: number;
  seats_available: number;
  status: RideRequestStatus;
  origin_lat: number;
  origin_lng: number;
  origin_address: string;
  destination_lat: number;
  destination_lng: number;
  destination_address: string;
  departure_at: string;
  expires_at: string;
  note?: string | null;
  women_only: boolean;
  route_polyline?: string | null;
  route_distance_km?: number | null;
  route_duration_min?: number | null;
  estimated_fare_total?: number | null;
  estimated_fare_solo?: number | null;
  created_at: string;
  locked_at?: string | null;
  members: RideMember[];
  driver?: RideDriver | null;
  ride?: RideInfo | null;
  dispatch?: DispatchInfo | null;
  my_role?: MemberRole | null;
  my_status?: MemberStatus | null;
  my_code?: string | null;
  my_code_kind?: 'otp' | 'matching_code' | null;
  my_fare_share_inr?: number | null;
  my_savings_inr?: number | null;
}

export interface MatchInfo {
  compatible: boolean;
  score: number;
  detour_km: number;
  pickup_offset_km: number;
  drop_offset_km: number;
  time_delta_min: number;
  reason?: string | null;
}

export interface FeedItem {
  request: RideRequest;
  match?: MatchInfo | null;
}

export interface DriverOffer {
  offer_id: string;
  request_id: string;
  expires_at: string;
  timeout_seconds: number;
  vehicle_type: VehicleType;
  vehicle_label: string;
  passenger_count: number;
  stops: number;
  pickup_lat: number;
  pickup_lng: number;
  pickup_address: string;
  destination_address: string;
  destination_lat: number;
  destination_lng: number;
  distance_to_pickup_km: number;
  eta_to_pickup_min: number;
  route_distance_km?: number | null;
  route_duration_min?: number | null;
  fare_total_inr?: number | null;
  driver_payout_inr?: number | null;
  departure_at: string;
  college_id: string;
  note?: string | null;
  polyline?: string | null;
}

export interface TripStop {
  member_id: string;
  user_id: string;
  full_name: string;
  phone?: string | null;
  seats: number;
  role: MemberRole;
  status: MemberStatus;
  code_kind: 'otp' | 'matching_code';
  matching_code?: string | null;
  fare_share_inr?: number | null;
  kind: 'pickup' | 'drop';
  order: number;
  lat: number;
  lng: number;
  address: string;
  eta_min?: number | null;
}

export interface TripView {
  ride: {
    id: string;
    status: RideStatus;
    started_at?: string | null;
    completed_at?: string | null;
    driver_eta_min?: number | null;
    total_fare_inr?: number | null;
    driver_payout_inr?: number | null;
    total_distance_km?: number | null;
  };
  request: RideRequest;
  stops: TripStop[];
  next_stop?: TripStop | null;
  rider_positions: LivePosition[];
  passengers_on_board: number;
}

export interface DriverEarnings {
  today_rides: number;
  today_earnings_inr: number;
  total_rides: number;
  total_earnings_inr: number;
  rating: number;
  acceptance_rate: number;
}

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  data: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface PlaceSuggestion {
  name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  place_id?: string | null;
  category?: string | null;
  distance_km?: number | null;
}

export interface RealtimeMessage<T = any> {
  type: string;
  payload: T;
  ts: number;
}

export interface TimelineEvent {
  id: string;
  event: string;
  actor_id?: string | null;
  data: Record<string, unknown>;
  created_at: string;
}
