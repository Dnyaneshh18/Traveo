import type { RideRequestStatus, VehicleType } from './types';

export interface VehicleMeta {
  type: VehicleType;
  label: string;
  capacity: number;
  emoji: string;
  description: string;
}

export const VEHICLES: VehicleMeta[] = [
  { type: 'auto', label: 'Auto Rickshaw', capacity: 3, emoji: '🛺', description: 'Cheapest for short hops' },
  { type: 'car', label: 'Car', capacity: 4, emoji: '🚗', description: 'AC comfort, 4 seats' },
  { type: 'car_xl', label: 'Car XL', capacity: 6, emoji: '🚐', description: 'Big group, 6 seats' },
  { type: 'bike', label: 'Bike', capacity: 1, emoji: '🏍️', description: 'Solo, fastest' },
];

export const VEHICLE_BY_TYPE: Record<VehicleType, VehicleMeta> = Object.fromEntries(
  VEHICLES.map((v) => [v.type, v]),
) as Record<VehicleType, VehicleMeta>;

export const STATUS_LABEL: Record<RideRequestStatus, string> = {
  open: 'Open for co-riders',
  locked: 'Finding driver',
  driver_assigned: 'Driver on the way',
  in_progress: 'Ride in progress',
  completed: 'Completed',
  no_driver: 'No driver found',
  cancelled: 'Cancelled',
  expired: 'Expired',
};

export const DEFAULT_CENTER = { lat: 18.5204, lng: 73.8567 }; // Pune
export const DEFAULT_ZOOM = 12;

export const WS_EVENTS = {
  connected: 'connected',
  feedCreated: 'feed.request_created',
  feedUpdated: 'feed.request_updated',
  feedRemoved: 'feed.request_removed',
  memberJoined: 'group.member_joined',
  memberLeft: 'group.member_left',
  locked: 'group.locked',
  reopened: 'group.reopened',
  removed: 'group.removed',
  dispatchStatus: 'dispatch.status',
  offer: 'dispatch.offer',
  offerExpired: 'dispatch.offer_expired',
  driverAssigned: 'ride.driver_assigned',
  driverLocation: 'ride.driver_location',
  riderLocation: 'ride.rider_location',
  driverArrived: 'ride.driver_arrived',
  pickedUp: 'ride.member_picked_up',
  dropped: 'ride.member_dropped',
  noShow: 'ride.member_no_show',
  completed: 'ride.completed',
  cancelled: 'ride.cancelled',
  driverCancelled: 'ride.driver_cancelled',
  noDriver: 'ride.no_driver',
  expired: 'ride.expired',
  notification: 'notification',
  profileUpdated: 'profile.updated',
} as const;

/** Events after which an active-ride screen should refetch from the API. */
export const RIDE_REFRESH_EVENTS: string[] = [
  WS_EVENTS.memberJoined,
  WS_EVENTS.memberLeft,
  WS_EVENTS.locked,
  WS_EVENTS.reopened,
  WS_EVENTS.removed,
  WS_EVENTS.dispatchStatus,
  WS_EVENTS.driverAssigned,
  WS_EVENTS.driverArrived,
  WS_EVENTS.pickedUp,
  WS_EVENTS.dropped,
  WS_EVENTS.noShow,
  WS_EVENTS.completed,
  WS_EVENTS.cancelled,
  WS_EVENTS.driverCancelled,
  WS_EVENTS.noDriver,
  WS_EVENTS.expired,
  'ride.updated',
];
