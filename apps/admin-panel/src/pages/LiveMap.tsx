import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import L from 'leaflet';
import { decodePolyline, formatDateTime, type LivePosition } from '@traveo/shared';
import { api, realtime } from '../lib/api';

const PUNE: [number, number] = [18.5204, 73.8567];

function icon(color: string, glyph: string, size = 30) {
  return L.divIcon({
    className: 'traveo-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:${size * 0.5}px">${glyph}</div>`,
  });
}

export function LiveMapPage() {
  const q = useQuery({ queryKey: ['live'], queryFn: async () => (await api.admin.live()).data, refetchInterval: 10000 });
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const driverMarkers = useRef<Map<string, L.Marker>>(new Map());
  const [events, setEvents] = useState<{ t: string; type: string; text: string }[]>([]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, { center: PUNE, zoom: 12 });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // Static layer: requests (routes, pickups) + drivers snapshot
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer || !q.data) return;
    layer.clearLayers();
    for (const r of q.data.requests) {
      if (r.polyline) L.polyline(decodePolyline(r.polyline).map((p) => [p.lat, p.lng] as [number, number]), { color: r.status === 'open' ? '#0EA5E9' : r.status === 'locked' ? '#F59E0B' : '#4F46E5', weight: 4, opacity: 0.8 }).addTo(layer);
      L.marker([r.origin.lat, r.origin.lng], { icon: icon('#16A34A', '▲', 26) }).bindPopup(`<b>${r.status}</b><br/>${r.origin.address}<br/>→ ${r.destination.address}<br/>${r.seats_taken}/${r.seat_capacity} seats · ${r.vehicle_type}`).addTo(layer);
      L.marker([r.destination.lat, r.destination.lng], { icon: icon('#DC2626', '■', 26) }).addTo(layer);
      if (r.status === 'locked' && r.dispatch_radius_km) L.circle([r.origin.lat, r.origin.lng], { radius: r.dispatch_radius_km * 1000, color: '#F59E0B', fillOpacity: 0.06, weight: 1.5, dashArray: '6 6' }).addTo(layer);
    }
    for (const d of q.data.drivers) {
      if (d.lat == null) continue;
      const m = driverMarkers.current.get(d.user_id);
      if (m) m.setLatLng([d.lat, d.lng]);
      else driverMarkers.current.set(d.user_id, L.marker([d.lat, d.lng], { icon: icon(d.status === 'on_trip' ? '#4F46E5' : '#0EA5E9', '🚕', 32), zIndexOffset: 1000 }).bindPopup(`<b>${d.name}</b><br/>${d.vehicle_type} · ${d.registration}<br/>${d.status}`).addTo(map));
    }
    for (const p of q.data.rider_positions as LivePosition[]) L.marker([p.lat, p.lng], { icon: icon('#8B5CF6', '🧑‍🎓', 26) }).addTo(layer);
  }, [q.data]);

  // Realtime: move driver markers instantly + event feed
  useEffect(() => {
    const push = (type: string, text: string) => setEvents((e) => [{ t: new Date().toISOString(), type, text }, ...e].slice(0, 60));
    const offs = [
      realtime.on('driver.location', (p: LivePosition) => {
        const map = mapRef.current;
        if (!map) return;
        const m = driverMarkers.current.get(p.user_id);
        if (m) m.setLatLng([p.lat, p.lng]);
        else driverMarkers.current.set(p.user_id, L.marker([p.lat, p.lng], { icon: icon('#0EA5E9', '🚕', 32), zIndexOffset: 1000 }).addTo(map));
      }),
      realtime.on('dispatch.status', (p) => push('dispatch', `Dispatch ${p.phase ?? ''} · ${p.radius_km ?? '?'} km · request ${String(p.request_id).slice(0, 6)}`)),
      realtime.on('request.created', (p) => push('request', `New request ${String(p.request_id).slice(0, 6)}`)),
      realtime.on('ride.driver_assigned', (p) => push('ride', `Driver assigned · ride ${String(p.ride_id).slice(0, 6)}`)),
      realtime.on('ride.completed', (p) => push('ride', `Ride completed · ₹${p.fare}`)),
      realtime.on('request.cancelled', (p) => push('cancel', `Request cancelled ${String(p.request_id).slice(0, 6)}`)),
      realtime.on('ride.driver_cancelled', (p) => push('cancel', `Driver cancelled · re-dispatching ${String(p.request_id).slice(0, 6)}`)),
      realtime.on('driver.status', (p) => push('driver', `Driver ${String(p.user_id).slice(0, 6)} is ${p.status}`)),
    ];
    return () => offs.forEach((o) => o());
  }, []);

  const counts = useMemo(() => ({
    drivers: q.data?.drivers.length ?? 0,
    onTrip: q.data?.drivers.filter((d: any) => d.status === 'on_trip').length ?? 0,
    open: q.data?.requests.filter((r: any) => r.status === 'open').length ?? 0,
    dispatching: q.data?.requests.filter((r: any) => r.status === 'locked').length ?? 0,
    live: q.data?.requests.filter((r: any) => r.status === 'driver_assigned' || r.status === 'in_progress').length ?? 0,
  }), [q.data]);

  return (
    <>
      <div className="page-head">
        <div><h1>Live map</h1><p className="sub">{counts.drivers} drivers online ({counts.onTrip} on trip) · {counts.open} open · {counts.dispatching} dispatching · {counts.live} live rides</p></div>
      </div>
      <div className="grid two">
        <div>
          <div ref={containerRef} className="map" />
          <div className="legend">
            <span style={{ ['--c' as any]: '#0EA5E9' }}>Driver online</span>
            <span style={{ ['--c' as any]: '#4F46E5' }}>Driver on trip</span>
            <span style={{ ['--c' as any]: '#16A34A' }}>Pickup / campus</span>
            <span style={{ ['--c' as any]: '#DC2626' }}>Destination</span>
            <span style={{ ['--c' as any]: '#8B5CF6' }}>Rider live</span>
            <span style={{ ['--c' as any]: '#F59E0B' }}>Dispatch radius</span>
          </div>
        </div>
        <div className="card">
          <h2>Event stream</h2>
          <div className="feed">
            {events.length === 0 ? <div className="empty">Waiting for realtime events…</div> : events.map((e, i) => (
              <div key={i} className="item"><div className="t">{formatDateTime(e.t)} · {e.type}</div>{e.text}</div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
