import * as Location from 'expo-location';
import { Platform } from 'react-native';
import type { LatLng } from '@traveo/shared';

export interface Fix extends LatLng {
  heading?: number | null;
  speed?: number | null;
  accuracy?: number | null;
}

export async function ensureLocationPermission(): Promise<boolean> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    return status === 'granted';
  } catch {
    return false;
  }
}

export async function getCurrentFix(): Promise<Fix | null> {
  // Web fallback: use standard browser navigator.geolocation directly if available
  if (Platform.OS === 'web' && typeof navigator !== 'undefined' && navigator.geolocation) {
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 4000,
          maximumAge: 30000,
        });
      });
      return {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        heading: pos.coords.heading,
        speed: pos.coords.speed,
        accuracy: pos.coords.accuracy,
      };
    } catch {
      // Fall through to Pune campus default for web previews
    }
  }

  try {
    if (!(await ensureLocationPermission())) {
      if (Platform.OS === 'web') {
        // Fallback to Pune default coordinates (VIT campus perimeter) in web preview
        return { lat: 18.4638, lng: 73.8680, heading: 0, speed: 0, accuracy: 10 };
      }
      return null;
    }
    const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    return {
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      heading: pos.coords.heading,
      speed: pos.coords.speed,
      accuracy: pos.coords.accuracy,
    };
  } catch {
    if (Platform.OS === 'web') {
      return { lat: 18.4638, lng: 73.8680, heading: 0, speed: 0, accuracy: 10 };
    }
    return null;
  }
}

/** Watch position; returns a stop function. */
export async function watchPosition(cb: (fix: Fix) => void, intervalMs = 4000): Promise<() => void> {
  // On web, use native navigator.geolocation.watchPosition directly:
  // expo-location's watchPositionAsync on web has an EventEmitter bug when unsubscribing
  // (_LocationEventEmitter.LocationEventEmitter.removeSubscription is not a function).
  if (Platform.OS === 'web' && typeof navigator !== 'undefined' && navigator.geolocation) {
    try {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => {
          cb({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            heading: pos.coords.heading,
            speed: pos.coords.speed,
            accuracy: pos.coords.accuracy,
          });
        },
        (err) => {
          console.warn('Geolocation watch error (using fallback):', err.message);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 5000 }
      );
      return () => {
        try {
          navigator.geolocation.clearWatch(watchId);
        } catch {
          /* ignore */
        }
      };
    } catch {
      return () => {};
    }
  }

  if (!(await ensureLocationPermission())) return () => {};
  try {
    const sub = await Location.watchPositionAsync(
      {
        accuracy: Platform.OS === 'web' ? Location.Accuracy.Balanced : Location.Accuracy.High,
        timeInterval: intervalMs,
        distanceInterval: 5,
      },
      (pos) =>
        cb({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          heading: pos.coords.heading,
          speed: pos.coords.speed,
          accuracy: pos.coords.accuracy,
        }),
    );
    return () => {
      try {
        if (sub && typeof sub.remove === 'function') {
          sub.remove();
        }
      } catch (e) {
        console.warn('Location sub.remove suppressed:', e);
      }
    };
  } catch (e) {
    console.warn('watchPositionAsync failed:', e);
    return () => {};
  }
}
