import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatDateTime, formatINR, formatKm, STATUS_LABEL, type RideRequest } from '@traveo/shared';
import { api } from '../lib/api';
import { useStore } from '../lib/store';
import { Drawer, Pill, When } from '../components/ui';

export function RidesPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const [status, setStatus] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const list = useQuery({ queryKey: ['rides', status], queryFn: async () => (await api.admin.rides({ status: status || undefined, limit: 100 })).data, refetchInterval: 10000 });
  const detail = useQuery({ queryKey: ['ride', selectedId], queryFn: async () => (await api.admin.ride(selectedId!)).data, enabled: !!selectedId, refetchInterval: 5000 });
  const cancel = useMutation({ mutationFn: (id: string) => api.admin.cancelRide(id), onSuccess: () => { notify('Ride cancelled'); qc.invalidateQueries({ queryKey: ['rides'] }); setSelectedId(null); } });
  const d = detail.data;
  return (
    <>
      <div className="page-head"><div><h1>Rides</h1><p className="sub">Every passenger group, from feed to completion.</p></div></div>
      <div className="toolbar">
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <span className="small">{list.data?.length ?? 0} rides</span>
      </div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Route</th><th>College</th><th>Vehicle</th><th>Seats</th><th>Status</th><th>Fare</th><th>Departure</th><th /></tr></thead>
          <tbody>
            {(list.data ?? []).map((r: RideRequest) => (
              <tr key={r.id}>
                <td><b>{r.origin_address.split(',')[0]}</b> → <b>{r.destination_address.split(',')[0]}</b><div className="small">{formatKm(r.route_distance_km)} · {r.direction.replace('_', ' ')}</div></td>
                <td>{r.college_name}</td>
                <td>{r.vehicle_label}</td>
                <td>{r.seats_taken}/{r.seat_capacity}</td>
                <td><Pill value={r.status} /></td>
                <td>{formatINR(r.estimated_fare_total)}</td>
                <td><When iso={r.departure_at} /></td>
                <td><button className="btn sm" onClick={() => setSelectedId(r.id)}>Inspect</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selectedId ? (
        <Drawer title={d ? `${d.origin_address.split(',')[0]} → ${d.destination_address.split(',')[0]}` : 'Ride'} onClose={() => setSelectedId(null)}>
          {!d ? <div className="empty">Loading…</div> : (
            <>
              <dl className="kv">
                <dt>Status</dt><dd><Pill value={d.status} /></dd>
                <dt>College</dt><dd>{d.college_name}</dd>
                <dt>Vehicle</dt><dd>{d.vehicle_label} · {d.seats_taken}/{d.seat_capacity} seats</dd>
                <dt>Route</dt><dd>{formatKm(d.route_distance_km)} · {Math.round(d.route_duration_min ?? 0)} min · fare {formatINR(d.estimated_fare_total)}</dd>
                <dt>Departure</dt><dd>{formatDateTime(d.departure_at)}</dd>
                <dt>Boarding OTP</dt><dd className="mono">{d.otp ?? '— (issued when a driver is assigned)'}</dd>
                {d.driver ? <><dt>Driver</dt><dd>{d.driver.full_name} · {d.driver.registration_number} · ★ {d.driver.rating}</dd></> : null}
                {d.dispatch ? <><dt>Dispatch</dt><dd>radius {d.dispatch.radius_km ?? '—'} km · {d.dispatch.attempts} offers</dd></> : null}
              </dl>
              <h2 style={{ marginTop: 18 }}>Members</h2>
              <table>
                <thead><tr><th>Name</th><th>Role</th><th>Status</th><th>Pickup → Drop</th><th>Share</th></tr></thead>
                <tbody>
                  {d.members.map((m: any) => (
                    <tr key={m.id}><td>{m.full_name}</td><td>{m.role}</td><td><Pill value={m.status} /></td><td className="small">{m.pickup_address.split(',')[0]} → {m.drop_address.split(',')[0]}{m.pickup_order ? ` · stop ${m.pickup_order}` : ''}</td><td>{formatINR(m.fare_share_inr)}</td></tr>
                  ))}
                </tbody>
              </table>
              <h2 style={{ marginTop: 18 }}>Driver offers</h2>
              {d.offers?.length ? (
                <table><thead><tr><th>Driver</th><th>Ring</th><th>ETA</th><th>Score</th><th>Result</th></tr></thead>
                  <tbody>{d.offers.map((o: any) => <tr key={o.id}><td className="mono">{o.driver_user_id.slice(0, 8)}</td><td>{o.radius_km} km</td><td>{o.eta_min} min</td><td>{o.score}</td><td><Pill value={o.status} /></td></tr>)}</tbody></table>
              ) : <p className="small muted">No offers yet.</p>}
              <h2 style={{ marginTop: 18 }}>Timeline</h2>
              <ul className="timeline">
                {d.timeline.map((e: any) => <li key={e.id}><span className="small">{formatDateTime(e.created_at)}</span><span><b>{e.event}</b> {Object.keys(e.data || {}).length ? <span className="small mono">{JSON.stringify(e.data)}</span> : null}</span></li>)}
              </ul>
              {['open', 'locked', 'driver_assigned', 'no_driver'].includes(d.status) ? (
                <div className="toolbar" style={{ marginTop: 16 }}><button className="btn danger" onClick={() => cancel.mutate(d.id)}>Cancel ride (ops)</button></div>
              ) : null}
            </>
          )}
        </Drawer>
      ) : null}
    </>
  );
}
