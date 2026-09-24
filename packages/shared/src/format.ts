export function formatINR(value: number | null | undefined, opts: { compact?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '₹—';
  const rounded = Math.round(value);
  if (opts.compact && rounded >= 1000) return `₹${(rounded / 1000).toFixed(1)}k`;
  return `₹${rounded.toLocaleString('en-IN')}`;
}

export function formatKm(km: number | null | undefined): string {
  if (km === null || km === undefined) return '—';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(km < 10 ? 1 : 0)} km`;
}

export function formatMinutes(min: number | null | undefined): string {
  if (min === null || min === undefined) return '—';
  const m = Math.round(min);
  if (m < 1) return 'now';
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export function formatTime(iso: string | Date | null | undefined): string {
  if (!iso) return '—';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  return d.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' });
}

export function formatDateTime(iso: string | Date | null | undefined): string {
  if (!iso) return '—';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
}

export function timeAgo(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  const diff = Math.max(0, Date.now() - d.getTime());
  const s = Math.floor(diff / 1000);
  if (s < 45) return 'just now';
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} h ago`;
  return `${Math.floor(h / 24)} d ago`;
}

export function departureLabel(iso: string): string {
  const d = new Date(iso);
  const diffMin = Math.round((d.getTime() - Date.now()) / 60000);
  if (diffMin <= -5) return `Left ${formatTime(d)}`;
  if (diffMin <= 2) return 'Leaving now';
  if (diffMin < 60) return `Leaves in ${diffMin} min`;
  return `Leaves ${formatTime(d)}`;
}

export function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('');
}

export function maskPhone(phone?: string | null): string {
  if (!phone) return '';
  return phone.replace(/^(\+\d{2})(\d{2})\d{4}(\d{4})$/, '$1 $2•••• $3');
}
