import type { Place } from '@traveo/shared';

export type AuthStackParamList = {
  Welcome: undefined;
  Phone: undefined;
  Otp: { phone: string; devOtp: string | null };
};

export type HomeTabParamList = {
  Home: undefined;
  Feed: undefined;
  Activity: undefined;
  Profile: undefined;
};

export type AppStackParamList = {
  Tabs: undefined;
  CreateRide: { origin?: Place; destination?: Place } | undefined;
  JoinRide: { requestId: string; pickup?: Place; drop?: Place };
  Ride: { requestId: string };
  RideComplete: { requestId: string };
  Notifications: undefined;
  History: undefined;
};
