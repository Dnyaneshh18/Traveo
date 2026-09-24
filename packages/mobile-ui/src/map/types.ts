import type { StyleProp, ViewStyle } from 'react-native';
import type { LatLng } from '@traveo/shared';

export type MarkerKind = 'driver' | 'rider' | 'me' | 'pickup' | 'drop' | 'campus' | 'stop';

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  kind: MarkerKind;
  label?: string; // short text shown inside/near the marker (e.g. "1", "You")
  heading?: number | null;
  color?: string;
}

export interface MapViewProps {
  style?: StyleProp<ViewStyle>;
  center?: LatLng;
  zoom?: number;
  markers?: MapMarker[];
  polyline?: LatLng[];
  polylineColor?: string;
  /** Fit the camera to these points whenever the array identity changes. */
  fitTo?: LatLng[] | null;
  fitPadding?: number;
  showUserLocation?: boolean;
  followUser?: boolean;
  interactive?: boolean;
  onPress?: (point: LatLng) => void;
  onMapError?: (message: string) => void;
  onReady?: () => void;
}
