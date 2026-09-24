import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { College } from '@traveo/shared';
import { api } from '../lib/api';
import { useStore } from '../lib/store';
import { Drawer, Pill } from '../components/ui';

const EMPTY = { code: '', name: '', short_name: '', aliases: '', institution_type: 'college', city: 'Pune', state: 'Maharashtra', address: '', latitude: 18.52, longitude: 73.85, id_pattern: '', id_hint: '', is_active: true };

export function CollegesPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const list = useQuery({ queryKey: ['colleges'], queryFn: async () => (await api.admin.colleges()).data });
  const [editing, setEditing] = useState<any | null>(null);
  const save = useMutation({
    mutationFn: async (c: any) => {
      const body = { ...c, aliases: String(c.aliases || '').split('|').map((a: string) => a.trim()).filter(Boolean), id_pattern: c.id_pattern || null, id_hint: c.id_hint || null, latitude: Number(c.latitude), longitude: Number(c.longitude) };
      return c.id ? api.admin.updateCollege(c.id, body) : api.admin.createCollege(body);
    },
    onSuccess: () => { notify('College saved'); qc.invalidateQueries({ queryKey: ['colleges'] }); setEditing(null); },
    onError: (e: any) => notify(e?.message || 'Save failed'),
  });
  const edit = (c: College) => setEditing({ ...c, aliases: c.aliases.join(' | ') });
  return (
    <>
      <div className="page-head">
        <div><h1>Colleges & schools</h1><p className="sub">The registry that scopes ride visibility. Aliases and the ID pattern drive automatic identity verification.</p></div>
        <button className="btn primary" onClick={() => setEditing({ ...EMPTY })}>+ Add institution</button>
      </div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Code</th><th>Name</th><th>Type</th><th>City</th><th>ID format</th><th>Aliases</th><th>Status</th><th /></tr></thead>
          <tbody>
            {(list.data ?? []).map((c) => (
              <tr key={c.id}>
                <td className="mono">{c.code}</td>
                <td><b>{c.name}</b><div className="small">{c.short_name} · {c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}</div></td>
                <td>{c.institution_type}</td>
                <td>{c.city}</td>
                <td><span className="small">{c.id_hint || '—'}</span></td>
                <td className="small">{c.aliases.join(', ')}</td>
                <td><Pill value={c.is_active ? 'verified' : 'rejected'} /></td>
                <td><button className="btn sm" onClick={() => edit(c)}>Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing ? (
        <Drawer title={editing.id ? `Edit ${editing.code}` : 'New institution'} onClose={() => setEditing(null)}>
          {[
            ['code', 'Code (unique)'], ['name', 'Official name'], ['short_name', 'Short name'], ['aliases', 'Aliases (separate with |)'], ['city', 'City'], ['state', 'State'], ['address', 'Address'],
            ['latitude', 'Latitude'], ['longitude', 'Longitude'], ['id_pattern', 'Student ID regex (e.g. ^\\d{9}$)'], ['id_hint', 'ID example shown to students'],
          ].map(([k, label]) => (
            <div key={k} style={{ marginBottom: 10 }}>
              <label className="small">{label}</label>
              <input className="input" style={{ width: '100%' }} value={editing[k] ?? ''} onChange={(e) => setEditing({ ...editing, [k]: e.target.value })} />
            </div>
          ))}
          <div style={{ marginBottom: 10 }}>
            <label className="small">Type</label>
            <select className="input" value={editing.institution_type} onChange={(e) => setEditing({ ...editing, institution_type: e.target.value })}><option value="college">College</option><option value="school">School</option></select>
          </div>
          <label className="small"><input type="checkbox" checked={!!editing.is_active} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Active</label>
          <div className="toolbar" style={{ marginTop: 16 }}><button className="btn primary" onClick={() => save.mutate(editing)} disabled={save.isPending}>Save</button></div>
        </Drawer>
      ) : null}
    </>
  );
}
