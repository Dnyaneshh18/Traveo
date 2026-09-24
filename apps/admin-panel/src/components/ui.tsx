import type { ReactNode } from 'react';
import { formatDateTime } from '@traveo/shared';

export const Pill = ({ value }: { value: string }) => <span className={`pill ${value}`}>{value.replace('_', ' ')}</span>;

export function Kpi({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card kpi">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}

export function Drawer({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <>
      <div className="backdrop" onClick={onClose} />
      <div className="drawer">
        <div className="page-head"><h1 style={{ fontSize: 20 }}>{title}</h1><button className="btn sm" onClick={onClose}>Close ✕</button></div>
        {children}
      </div>
    </>
  );
}

export const When = ({ iso }: { iso?: string | null }) => <span className="small">{iso ? formatDateTime(iso) : '—'}</span>;
