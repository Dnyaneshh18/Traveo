import { useEffect } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { bindConnection, useStore } from './lib/store';
import { realtime } from './lib/api';
import { LoginPage } from './pages/Login';
import { DashboardPage } from './pages/Dashboard';
import { LiveMapPage } from './pages/LiveMap';
import { StudentsPage } from './pages/Students';
import { DriversPage } from './pages/Drivers';
import { RidesPage } from './pages/Rides';
import { CollegesPage } from './pages/Colleges';
import { ConfigPage } from './pages/Config';

const NAV = [
  ['/', '📊', 'Dashboard'],
  ['/live', '🗺️', 'Live map'],
  ['/rides', '🚕', 'Rides'],
  ['/students', '🎓', 'Students'],
  ['/drivers', '🪪', 'Drivers'],
  ['/colleges', '🏫', 'Colleges'],
  ['/config', '⚙️', 'Ride engine'],
] as const;

export function App() {
  const status = useStore((s) => s.status);
  const hydrate = useStore((s) => s.hydrate);
  const logout = useStore((s) => s.logout);
  const user = useStore((s) => s.user);
  const connection = useStore((s) => s.connection);
  const toast = useStore((s) => s.toast);
  const qc = useQueryClient();

  useEffect(() => {
    hydrate();
    bindConnection();
  }, [hydrate]);

  // Any realtime event → refresh the relevant admin queries.
  useEffect(() => {
    if (status !== 'in') return;
    return realtime.onAny((_p, msg) => {
      if (msg.type.startsWith('driver.') || msg.type.startsWith('rider.')) qc.invalidateQueries({ queryKey: ['live'] });
      else qc.invalidateQueries();
    });
  }, [status, qc]);

  if (status === 'loading') return <div className="empty">Loading…</div>;
  if (status === 'out') return <LoginPage />;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span>🎓🛺</span>
          <div>Traveo<small>Ops console</small></div>
        </div>
        <nav className="nav">
          {NAV.map(([to, icon, label]) => (
            <NavLink key={to} to={to} end={to === '/'}>
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="spacer" />
        <div className="status"><span className={`dot ${connection}`} /> realtime {connection}</div>
        <div className="status">{user?.full_name} · <button className="btn sm" onClick={logout}>Sign out</button></div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/live" element={<LiveMapPage />} />
          <Route path="/rides" element={<RidesPage />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/drivers" element={<DriversPage />} />
          <Route path="/colleges" element={<CollegesPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  );
}
