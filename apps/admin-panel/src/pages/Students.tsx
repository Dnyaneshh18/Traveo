import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useStore } from '../lib/store';
import { Drawer, Pill, When } from '../components/ui';

export function StudentsPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const [status, setStatus] = useState<string>('pending');
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<any | null>(null);
  const [note, setNote] = useState('');
  const list = useQuery({ queryKey: ['students', status, q], queryFn: async () => (await api.admin.students({ status: status || undefined, q: q || undefined, limit: 100 })).data });
  const verify = useMutation({
    mutationFn: ({ id, status, note }: { id: string; status: string; note?: string }) => api.admin.verifyStudent(id, status, note),
    onSuccess: (_d, v) => { notify(`Student ${v.status}`); qc.invalidateQueries({ queryKey: ['students'] }); qc.invalidateQueries({ queryKey: ['dashboard'] }); setSelected(null); },
  });
  const toggle = useMutation({ mutationFn: ({ id, active }: { id: string; active: boolean }) => api.admin.toggleUser(id, active), onSuccess: () => { notify('Updated'); qc.invalidateQueries({ queryKey: ['students'] }); } });

  return (
    <>
      <div className="page-head">
        <div><h1>Students</h1><p className="sub">Identity verification queue — college name on ID must match the selected college; ID format is checked against the college pattern.</p></div>
      </div>
      <div className="toolbar">
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="pending">Pending review</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
          <option value="">All</option>
        </select>
        <input className="input" placeholder="Search name / phone / ID" value={q} onChange={(e) => setQ(e.target.value)} />
        <span className="small">{list.data?.length ?? 0} students</span>
      </div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Student</th><th>College</th><th>ID number</th><th>Name on ID</th><th>Match</th><th>Status</th><th>Joined</th><th /></tr></thead>
          <tbody>
            {(list.data ?? []).map((s) => (
              <tr key={s.id}>
                <td><b>{s.full_name || '—'}</b><div className="small">{s.phone}{s.gender ? ` · ${s.gender}` : ''}{s.course ? ` · ${s.course}` : ''}</div></td>
                <td>{s.college.short_name || s.college.name}</td>
                <td className="mono">{s.college_id_number}</td>
                <td>{s.college_name_on_id}</td>
                <td><b>{Math.round(s.identity_match_score * 100)}%</b>{s.id_card_url ? <div className="small">📎 ID uploaded</div> : <div className="small muted">no photo</div>}</td>
                <td><Pill value={s.verification_status} />{!s.is_active ? <div><Pill value="disabled" /></div> : null}</td>
                <td><When iso={s.created_at} /></td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  <button className="btn sm" onClick={() => { setSelected(s); setNote(''); }}>Review</button>{' '}
                  {s.verification_status !== 'verified' ? <button className="btn sm success" onClick={() => verify.mutate({ id: s.id, status: 'verified', note: 'Verified by ops' })}>Approve</button> : null}
                </td>
              </tr>
            ))}
            {list.data && list.data.length === 0 ? <tr><td colSpan={8} className="empty">Nothing here 🎉</td></tr> : null}
          </tbody>
        </table>
      </div>

      {selected ? (
        <Drawer title={selected.full_name || 'Student'} onClose={() => setSelected(null)}>
          <dl className="kv">
            <dt>Phone</dt><dd>{selected.phone}</dd>
            <dt>College</dt><dd>{selected.college.name}</dd>
            <dt>ID number</dt><dd className="mono">{selected.college_id_number}</dd>
            <dt>Name on ID</dt><dd>{selected.college_name_on_id}</dd>
            <dt>Identity match</dt><dd>{Math.round(selected.identity_match_score * 100)}% similarity to registry name/aliases</dd>
            <dt>Status</dt><dd><Pill value={selected.verification_status} /></dd>
            <dt>System note</dt><dd>{selected.verification_note}</dd>
            <dt>Rides</dt><dd>{selected.completed_rides} completed · ★ {selected.average_rating}</dd>
          </dl>
          {selected.id_card_url ? <img className="idcard" src={selected.id_card_url} alt="ID card" /> : <p className="small muted">No ID card photo uploaded yet.</p>}
          <label className="small" style={{ display: 'block', marginTop: 16, marginBottom: 6 }}>Note to student (optional)</label>
          <textarea className="input" style={{ width: '100%', minHeight: 70 }} value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Photo is blurry – please re-upload" />
          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn success" onClick={() => verify.mutate({ id: selected.id, status: 'verified', note: note || 'Verified by ops' })}>Approve ✓</button>
            <button className="btn danger" onClick={() => verify.mutate({ id: selected.id, status: 'rejected', note: note || 'Could not verify your ID card' })}>Reject</button>
            <button className="btn" onClick={() => toggle.mutate({ id: selected.user_id, active: !selected.is_active })}>{selected.is_active ? 'Disable account' : 'Enable account'}</button>
          </div>
        </Drawer>
      ) : null}
    </>
  );
}
