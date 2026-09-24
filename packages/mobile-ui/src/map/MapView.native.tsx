/**
 * MapView (Android) — Mappls (MapmyIndia) React-Native SDK.
 *
 * Requires a custom development build / prebuild (`npx expo run:android`) with the Mappls account files
 * (`<package>.a.conf` / `<package>.a.olf`) and native view managers compiled in.
 *
 * If running inside standard Expo Go or if native Mappls view managers (`RCTMGLMapView`, `RCTMGLCamera`)
 * are not compiled into the current binary, a graceful informative fallback is rendered instead of throwing
 * `Invariant Violation: View config not found for component RCTMGLCamera`.
 */
import React, { useEffect, useMemo, useRef } from 'react';
import { StyleSheet, Text, View, UIManager, Platform } from 'react-native';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import { boundsOf, colors, DEFAULT_CENTER, DEFAULT_ZOOM } from '@traveo/shared';
import type { MapViewProps } from './types';
import { MarkerGlyph } from './MarkerGlyph';

function checkMapplsNativeAvailable(): boolean {
  if (Platform.OS !== 'android') return false;

  // Expo Go does not compile 3rd-party custom native modules/views (like Mappls SDK)
  try {
    const isExpoGo =
      (Constants as any)?.appOwnership === 'expo' ||
      (Constants as any)?.executionEnvironment === ExecutionEnvironment.StoreClient;
    if (isExpoGo) {
      return false;
    }
  } catch {
    // ignore
  }

  // Ensure RCTMGLCamera and RCTMGLMapView are truly registered in the native UIManager
  try {
    const hasConfig =
      typeof UIManager?.getViewManagerConfig === 'function'
        ? !!UIManager.getViewManagerConfig('RCTMGLCamera') && !!UIManager.getViewManagerConfig('RCTMGLMapView')
        : !!(UIManager as any)?.RCTMGLCamera && !!(UIManager as any)?.RCTMGLMapView;
    return !!hasConfig;
  } catch {
    return false;
  }
}

const isNativeSupported = checkMapplsNativeAvailable();

let Mappls: any = null;
if (isNativeSupported) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    Mappls = require('mappls-map-react-native');
  } catch {
    Mappls = null;
  }
}

export default function MapView(props: MapViewProps) {
  if (!isNativeSupported || !Mappls || !Mappls.MapView) {
    return (
      <View style={[styles.fallback, props.style]}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Mappls Real-Time Map</Text>
        </View>
        <Text style={styles.fallbackTitle}>MapmyIndia SDK Ready</Text>
        <Text style={styles.fallbackBody}>
          Native map rendering requires a custom development build (`npx expo run:android`) or APK. In Expo Go, map preview is safely paused to prevent native crashes.
        </Text>
      </View>
    );
  }
  return <MapplsMap {...props} />;
}

function MapplsMap({
  style,
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  markers = [],
  polyline,
  polylineColor = colors.route,
  fitTo,
  fitPadding = 60,
  showUserLocation = false,
  followUser = false,
  interactive = true,
  onPress,
  onMapError,
  onReady,
}: MapViewProps) {
  const cameraRef = useRef<any>(null);
  const { MapView: MMapView, Camera, ShapeSource, LineLayer, MarkerView, UserLocation } = Mappls;

  useEffect(() => {
    if (!fitTo || fitTo.length === 0 || !cameraRef.current) return;
    const b = boundsOf(fitTo);
    if (!b) return;
    if (fitTo.length === 1) {
      cameraRef.current.setCamera({ centerCoordinate: [fitTo[0].lng, fitTo[0].lat], zoomLevel: 15, animationDuration: 600 });
      return;
    }
    cameraRef.current.fitBounds([b.ne.lng, b.ne.lat], [b.sw.lng, b.sw.lat], fitPadding, 700);
  }, [fitTo, fitPadding]);

  const lineShape = useMemo(
    () =>
      polyline && polyline.length > 1
        ? { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: polyline.map((p) => [p.lng, p.lat]) } }
        : null,
    [polyline],
  );

  return (
    <MMapView
      style={[styles.map, style]}
      logoEnabled
      attributionEnabled={false}
      compassEnabled={false}
      zoomEnabled={interactive}
      scrollEnabled={interactive}
      rotateEnabled={false}
      pitchEnabled={false}
      onDidFinishLoadingMap={onReady}
      onMapError={(e: any) => onMapError?.(e?.message || e?.errorCode?.toString?.() || 'Map failed to load')}
      onPress={(feature: any) => {
        const c = feature?.geometry?.coordinates;
        if (c && onPress) onPress({ lng: c[0], lat: c[1] });
      }}
    >
      <Camera
        ref={cameraRef}
        defaultSettings={{ centerCoordinate: [center.lng, center.lat], zoomLevel: zoom }}
        followUserLocation={followUser}
        followZoomLevel={16}
        animationMode="flyTo"
        animationDuration={500}
      />
      {showUserLocation ? <UserLocation visible androidRenderMode="compass" showsUserHeadingIndicator /> : null}
      {lineShape ? (
        <ShapeSource id="traveo-route" shape={lineShape}>
          <LineLayer id="traveo-route-casing" style={{ lineColor: '#ffffff', lineWidth: 8, lineCap: 'round', lineJoin: 'round', lineOpacity: 0.9 }} />
          <LineLayer id="traveo-route-line" style={{ lineColor: polylineColor, lineWidth: 5, lineCap: 'round', lineJoin: 'round' }} />
        </ShapeSource>
      ) : null}
      {markers.map((m) => (
        <MarkerView key={m.id} id={m.id} coordinate={[m.lng, m.lat]} anchor={{ x: 0.5, y: m.kind === 'driver' || m.kind === 'me' ? 0.5 : 1 }}>
          <MarkerGlyph marker={m} />
        </MarkerView>
      ))}
    </MMapView>
  );
}

const styles = StyleSheet.create({
  map: { flex: 1 },
  fallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F1F5F9',
    padding: 24,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    margin: 8,
  },
  badge: {
    backgroundColor: '#E0E7FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4338CA',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  fallbackTitle: {
    fontWeight: '700',
    fontSize: 16,
    color: '#0F172A',
    marginBottom: 6,
  },
  fallbackBody: {
    color: '#64748B',
    textAlign: 'center',
    fontSize: 13,
    lineHeight: 18,
    maxWidth: 280,
  },
});
