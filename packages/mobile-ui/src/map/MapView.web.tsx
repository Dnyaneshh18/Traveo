/**
 * MapView (web) — Leaflet + OpenStreetMap tiles.  Used for `expo start --web`
 * demos and the admin panel; the Android build renders Mappls instead.
 */
import React, { useEffect, useMemo, useRef } from 'react';
import { View } from 'react-native';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { boundsOf, colors, DEFAULT_CENTER, DEFAULT_ZOOM } from '@traveo/shared';
import type { MapMarker, MapViewProps } from './types';

const KIND_COLOR: Record<MapMarker['kind'], string> = {
  driver: colors.driver,
  rider: colors.rider,
  me: colors.primary,
  pickup: colors.pickup,
  drop: colors.drop,
  campus: colors.campus,
  stop: colors.text,
};
const KIND_GLYPH: Record<MapMarker['kind'], string> = { driver: '🚗', rider: '🧑‍🎓', me: '', pickup: '▲', drop: '■', campus: '🎓', stop: '•' };

function iconFor(m: MapMarker): L.DivIcon {
  const color = m.color ?? KIND_COLOR[m.kind];
  if (m.kind === 'driver') {
    return L.divIcon({
      className: 'traveo-marker',
      iconSize: [40, 40],
      iconAnchor: [20, 20],
      html: `<div style="transform:rotate(${m.heading ?? 0}deg);width:40px;height:40px;display:flex;align-items:center;justify-content:center;">
        <div style="position:absolute;top:-4px;width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:12px solid ${color}"></div>
        <div style="width:34px;height:34px;border-radius:50%;background:${color};border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;font-size:16px">🚗</div></div>`,
    });
  }
  if (m.kind === 'me') {
    return L.divIcon({
      className: 'traveo-marker',
      iconSize: [26, 26],
      iconAnchor: [13, 13],
      html: `<div style="width:26px;height:26px;border-radius:50%;background:rgba(79,70,229,.2);display:flex;align-items:center;justify-content:center"><div style="width:14px;height:14px;border-radius:50%;background:${color};border:2.5px solid #fff"></div></div>`,
    });
  }
  return L.divIcon({
    className: 'traveo-marker',
    iconSize: [40, 46],
    iconAnchor: [20, 44],
    html: `<div style="display:flex;flex-direction:column;align-items:center;width:40px">
      <div style="min-width:32px;height:32px;padding:0 6px;border-radius:16px;background:${color};border:2.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:13px;font-family:system-ui">${m.label ?? KIND_GLYPH[m.kind]}</div>
      <div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:9px solid ${color};margin-top:-2px"></div></div>`,
  });
}

export default function MapView({
  style,
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  markers = [],
  polyline,
  polylineColor = colors.route,
  fitTo,
  fitPadding = 60,
  showUserLocation,
  followUser,
  interactive = true,
  onPress,
  onReady,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerLayer = useRef<Map<string, L.Marker>>(new Map());
  const lineRef = useRef<L.Polyline | null>(null);
  const onPressRef = useRef(onPress);
  onPressRef.current = onPress;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, {
      center: [center.lat, center.lng],
      zoom,
      zoomControl: false,
      attributionControl: false,
      dragging: interactive,
      scrollWheelZoom: interactive,
      touchZoom: interactive,
      doubleClickZoom: interactive,
    });
    // Standard reliable OSM mirror with no watermark
    L.tileLayer('https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '',
    }).addTo(map);
    map.on('click', (e: L.LeafletMouseEvent) => onPressRef.current?.({ lat: e.latlng.lat, lng: e.latlng.lng }));
    mapRef.current = map;
    onReady?.();
    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(containerRef.current);
    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
      markerLayer.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // markers diff
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const seen = new Set<string>();
    for (const m of markers) {
      seen.add(m.id);
      const existing = markerLayer.current.get(m.id);
      if (existing) {
        existing.setLatLng([m.lat, m.lng]);
        existing.setIcon(iconFor(m));
      } else {
        const mk = L.marker([m.lat, m.lng], { icon: iconFor(m), interactive: false, zIndexOffset: m.kind === 'driver' ? 1000 : 0 }).addTo(map);
        markerLayer.current.set(m.id, mk);
      }
    }
    for (const [id, mk] of markerLayer.current) {
      if (!seen.has(id)) {
        mk.remove();
        markerLayer.current.delete(id);
      }
    }
  }, [markers]);

  const lineKey = useMemo(() => (polyline ? polyline.map((p) => `${p.lat.toFixed(5)},${p.lng.toFixed(5)}`).join('|') : ''), [polyline]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    lineRef.current?.remove();
    lineRef.current = null;
    if (polyline && polyline.length > 1) {
      lineRef.current = L.polyline(polyline.map((p) => [p.lat, p.lng] as [number, number]), { color: polylineColor, weight: 5, opacity: 0.9, lineCap: 'round' }).addTo(map);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lineKey, polylineColor]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !fitTo || fitTo.length === 0) return;
    const b = boundsOf(fitTo);
    if (!b) return;
    if (fitTo.length === 1) map.flyTo([fitTo[0].lat, fitTo[0].lng], 15, { duration: 0.6 });
    else map.flyToBounds(L.latLngBounds([b.sw.lat, b.sw.lng], [b.ne.lat, b.ne.lng]), { padding: [fitPadding, fitPadding], duration: 0.7 });
  }, [fitTo, fitPadding]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || fitTo) return;
    map.setView([center.lat, center.lng], zoom, { animate: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center.lat, center.lng]);

  // followUser/showUserLocation are handled by the "me" marker on web.
  void showUserLocation;
  void followUser;

  return (
    <View style={[{ flex: 1, overflow: 'hidden' }, style]}>
      <style>{`.leaflet-control-attribution { display: none !important; }`}</style>
      <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: 160, background: '#E2E8F0' }} />
    </View>
  );
}
