import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatINR } from '@traveo/shared';
import { api } from '../lib/api';
import { useStore } from '../lib/store';
import { Pill, When } from '../components/ui';

export function DriversPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const [status, setStatus] = useState('');
  const list = useQuery({ queryKey: ['drivers', status], queryFn: async () => (await api.admin.drivers({ status: status || undefined, limit: 100 })).data, refetchInterval: 15000 });
  const verify = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.admin.verifyDriver(id, status),
    onSuccess: () => { notify('Driver updated'); qc.invalidateQueries({ queryKey: ['drivers'] }); },
  });
  const toggle = useMutation({ mutationFn: ({ id, active }: { id: string; active: boolean }) => api.admin.toggleUser(id, active), onSuccess: () => { notify('Updated'); qc.invalidateQueries({ queryKey: ['drivers'] }); } });
  return (
    <>
      <div className="page-head"><div><h1>Drivers</h1><p className="sub">Licence & vehicle verification, availability and performance.</p></div></div>
      <div className="toolbar">
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All</option><option value="pending">Pending</option><option value="verified">Verified</option><option value="rejected">Rejected</option>
        </select>
        <span className="small">{list.data?.length ?? 0} drivers</span>
      </div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Driver</th><th>Vehicle</th><th>Licence</th><th>Verification</th><th>Availability</th><th>Performance</th><th>Joined</th><th /></tr></thead>
          <tbody>
            {(list.data ?? []).map((d) => (
              <tr key={d.id}>
                <td><b>{d.full_name}</b><div className="small">{d.phone}</div></td>
                <td>{d.vehicle ? <><b>{d.vehicle.registration}</b><div className="small">{d.vehicle.type} · {d.vehicle.make_model ?? ''} {d.vehicle.color ?? ''}</div></> : '—'}</td>
                <td className="mono">{d.license_number}</td>
                <td><Pill value={d.verification_status} /></td>
                <td><Pill value={d.status} /></td>
                <td>{d.completed_rides} rides · ★ {d.average_rating.toFixed(1)}<div className="small">accept {Math.round(d.acceptance_rate * 100)}% · {formatINR(d.total_earnings_inr)}</div></td>
                <td><When iso={d.created_at} /></td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  {d.verification_status !== 'verified' ? <button className="btn sm success" onClick={() => verify.mutate({ id: d.id, status: 'verified' })}>Approve</button> : <button className="btn sm danger" onClick={() => verify.mutate({ id: d.id, status: 'rejected' })}>Revoke</button>}{' '}
                  <button className="btn sm" onClick={() => toggle.mutate({ id: d.user_id, active: !d.is_active })}>{d.is_active ? 'Disable' : 'Enable'}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
