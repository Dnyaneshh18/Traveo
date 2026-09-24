import { useQuery } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatINR } from '@traveo/shared';
import { api } from '../lib/api';
import { Kpi } from '../components/ui';

export function DashboardPage() {
  const q = useQuery({ queryKey: ['dashboard'], queryFn: async () => (await api.admin.dashboard()).data, refetchInterval: 15000 });
  const d = q.data;
  if (!d) return <div className="empty">Loading dashboard…</div>;
  return (
    <>
      <div className="page-head">
        <div><h1>Dashboard</h1><p className="sub">Live overview · maps provider: <b>{d.maps_provider}</b> · {d.realtime_connections} realtime connections</p></div>
      </div>
      <div className="grid kpis">
        <Kpi label="Open requests" value={d.rides.open_requests} hint="collecting co-riders" />
        <Kpi label="Dispatching" value={d.rides.dispatching} hint="searching drivers" />
        <Kpi label="Live rides" value={d.rides.live} hint="driver assigned / on trip" />
        <Kpi label="Rides today" value={d.rides.today} hint={`${d.rides.week} this week`} />
        <Kpi label="Drivers online" value={d.drivers.online} hint={`${d.drivers.total} total · ${d.drivers.pending} pending`} />
        <Kpi label="Students" value={d.students.total} hint={`${d.students.pending} awaiting verification`} />
        <Kpi label="GMV (7d)" value={formatINR(d.revenue.gmv_week_inr)} hint={`fees ${formatINR(d.revenue.platform_fees_week_inr)}`} />
        <Kpi label="Avg group size" value={d.avg_group_size} hint="seats per completed ride" />
      </div>
      <div className="grid two" style={{ marginTop: 16 }}>
        <div className="card">
          <h2>Completed rides · last 7 days</h2>
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={d.series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tickFormatter={(v: string) => v.slice(5)} fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="rides" fill="#4F46E5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <h2>Requests by college</h2>
          <table>
            <thead><tr><th>College</th><th style={{ textAlign: 'right' }}>Requests</th></tr></thead>
            <tbody>
              {d.per_college.map((r: any) => (
                <tr key={r.college}><td>{r.college}</td><td style={{ textAlign: 'right' }}><b>{r.requests}</b></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
