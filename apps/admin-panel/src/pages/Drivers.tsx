import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatINR } from '@traveo/shared';
import { api } from '../lib/api';
import { useStore } from '../lib/store';
import { Drawer, Pill, When } from '../components/ui';

export function DriversPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const [status, setStatus] = useState('');
  const [selected, setSelected] = useState<any | null>(null);
  const [note, setNote] = useState('');

  const list = useQuery({ queryKey: ['drivers', status], queryFn: async () => (await api.admin.drivers({ status: status || undefined, limit: 100 })).data, refetchInterval: 15000 });
  const verify = useMutation({
    mutationFn: ({ id, status, note }: { id: string; status: string; note?: string }) => api.admin.verifyDriver(id, status, note),
    onSuccess: (_d, v) => {
      notify(`Driver ${v.status}`);
      qc.invalidateQueries({ queryKey: ['drivers'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
      setSelected(null);
    },
  });
  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => api.admin.toggleUser(id, active),
    onSuccess: () => {
      notify('Updated');
      qc.invalidateQueries({ queryKey: ['drivers'] });
    },
  });

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
                <td><Pill value={d.verification_status} />{!d.is_active ? <div><Pill value="disabled" /></div> : null}</td>
                <td><Pill value={d.status} /></td>
                <td>{d.completed_rides} rides · ★ {d.average_rating.toFixed(1)}<div className="small">accept {Math.round(d.acceptance_rate * 100)}% · {formatINR(d.total_earnings_inr)}</div></td>
                <td><When iso={d.created_at} /></td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  <button className="btn sm" onClick={() => { setSelected(d); setNote(''); }}>Review</button>{' '}
                  {d.verification_status !== 'verified' ? (
                    <button className="btn sm success" onClick={() => verify.mutate({ id: d.id, status: 'verified', note: 'Verified by ops' })}>Approve</button>
                  ) : (
                    <button className="btn sm danger" onClick={() => verify.mutate({ id: d.id, status: 'rejected', note: 'Revoked by admin' })}>Revoke</button>
                  )}{' '}
                  <button className="btn sm" onClick={() => toggle.mutate({ id: d.user_id, active: !d.is_active })}>{d.is_active ? 'Disable' : 'Enable'}</button>
                </td>
              </tr>
            ))}
            {list.data && list.data.length === 0 ? <tr><td colSpan={8} className="empty">No drivers found 🎉</td></tr> : null}
          </tbody>
        </table>
      </div>

      {selected ? (
        <Drawer title={selected.full_name || 'Driver'} onClose={() => setSelected(null)}>
          <dl className="kv">
            <dt>Phone</dt><dd>{selected.phone}</dd>
            <dt>Licence number</dt><dd className="mono">{selected.license_number}</dd>
            <dt>Vehicle Type</dt><dd>{selected.vehicle?.type ?? '—'}</dd>
            <dt>Registration</dt><dd className="mono"><b>{selected.vehicle?.registration ?? '—'}</b></dd>
            <dt>Vehicle Details</dt><dd>{selected.vehicle?.make_model ?? '—'} {selected.vehicle?.color ? `(${selected.vehicle.color})` : ''}</dd>
            <dt>Status</dt><dd><Pill value={selected.verification_status} /></dd>
            <dt>Note</dt><dd>{selected.verification_note || '—'}</dd>
            <dt>Performance</dt><dd>{selected.completed_rides} completed rides · ★ {selected.average_rating}</dd>
          </dl>
          {selected.license_url ? <img className="idcard" src={selected.license_url} alt="Driving Licence" /> : <p className="small muted">No licence document photo uploaded.</p>}
          <label className="small" style={{ display: 'block', marginTop: 16, marginBottom: 6 }}>Reason / Note to driver</label>
          <textarea
            className="input"
            style={{ width: '100%', minHeight: 70 }}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Licence number mismatched, or approved for onboarding"
          />
          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn success" onClick={() => verify.mutate({ id: selected.id, status: 'verified', note: note || 'Verified by ops' })}>Approve ✓</button>
            <button className="btn danger" onClick={() => verify.mutate({ id: selected.id, status: 'rejected', note: note || 'Licence or vehicle details could not be verified' })}>Reject</button>
            <button className="btn" onClick={() => toggle.mutate({ id: selected.user_id, active: !selected.is_active })}>{selected.is_active ? 'Disable account' : 'Enable account'}</button>
          </div>
        </Drawer>
      ) : null}
    </>
  );
}
