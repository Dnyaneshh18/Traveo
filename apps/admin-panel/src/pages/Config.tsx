import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useStore } from '../lib/store';

export function ConfigPage() {
  const qc = useQueryClient();
  const notify = useStore((s) => s.notify);
  const q = useQuery({ queryKey: ['config'], queryFn: async () => (await api.admin.config()).data });
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const save = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => api.admin.setConfig(key, value),
    onSuccess: (_d, v) => { notify(`${v.key} saved`); qc.invalidateQueries({ queryKey: ['config'] }); setDrafts((d) => { const n = { ...d }; delete n[v.key]; return n; }); },
    onError: (e: any) => notify(e?.message || 'Save failed'),
  });
  const parse = (raw: string) => {
    try { return JSON.parse(raw); } catch { return raw; }
  };
  return (
    <>
      <div className="page-head"><div><h1>Ride engine configuration</h1><p className="sub">Live-tunable parameters of matching, dispatch and fares. Changes apply within 30 seconds.</p></div></div>
      <div className="card">
        {(q.data ?? []).map((c) => {
          const current = JSON.stringify(c.value);
          const draft = drafts[c.key] ?? current;
          return (
            <div key={c.key} className="config-row">
              <div><b className="mono">{c.key}</b><div className="small">{c.description}</div></div>
              <div className="small muted">default {JSON.stringify(c.default)}</div>
              <input className="input mono" value={draft} onChange={(e) => setDrafts({ ...drafts, [c.key]: e.target.value })} />
              <button className="btn sm primary" disabled={draft === current || save.isPending} onClick={() => save.mutate({ key: c.key, value: parse(draft) })}>Save</button>
            </div>
          );
        })}
      </div>
    </>
  );
}
