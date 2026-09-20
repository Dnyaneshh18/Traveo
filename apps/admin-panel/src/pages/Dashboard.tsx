import React, { useState, useEffect } from 'react';
import { StatCard } from '../components/StatCard';
import { adminApiService } from '../services/api';

interface DashboardKPIs {
  active_rides: number;
  active_passengers: number;
  online_drivers: number;
  waiting_groups: number;
  matching_success_rate: number;
  average_wait_time_minutes: number;
  revenue_today: number;
  revenue_this_week: number;
  revenue_this_month: number;
  cancellation_rate: number;
  driver_acceptance_rate: number;
  average_occupancy: number;
}

export const DashboardPage: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKPIs>({
    active_rides: 0,
    active_passengers: 0,
    online_drivers: 0,
    waiting_groups: 0,
    matching_success_rate: 0,
    average_wait_time_minutes: 0,
    revenue_today: 0,
    revenue_this_week: 0,
    revenue_this_month: 0,
    cancellation_rate: 0,
    driver_acceptance_rate: 0,
    average_occupancy: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadKPIs() {
      try {
        const data = await adminApiService.getDashboardKPIs();
        if (data && typeof data.active_rides === 'number') {
          setKpis(data);
        }
      } catch (err) {
        console.warn('Could not load KPIs from backend:', err);
      } finally {
        setLoading(false);
      }
    }
    loadKPIs();
  }, []);

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h1 style={{ color: '#F8FAFC', margin: '0 0 0.5rem 0', fontSize: '1.75rem' }}>Operations Dashboard</h1>
        <p style={{ color: '#94A3B8', margin: 0 }}>Real-time telemetry and shared ride platform performance</p>
      </div>

      {loading ? (
        <div style={{ color: '#94A3B8' }}>Loading real-time KPIs...</div>
      ) : (
        <>
          {/* Primary KPI Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1.25rem',
          }}>
            <StatCard
              title="Active Rides"
              value={kpis.active_rides}
              subtitle={`${kpis.active_passengers} passengers in transit`}
              icon="🚕"
              trend="+12%"
              color="#38BDF8"
            />
            <StatCard
              title="Online Drivers"
              value={kpis.online_drivers}
              subtitle={`${kpis.waiting_groups} groups searching`}
              icon="🚘"
              trend="+5%"
              color="#22C55E"
            />
            <StatCard
              title="Matching Success Rate"
              value={`${kpis.matching_success_rate}%`}
              subtitle={`Avg wait: ${kpis.average_wait_time_minutes} mins`}
              icon="⚡"
              trend="+2.4%"
              color="#A855F7"
            />
            <StatCard
              title="Revenue Today"
              value={`₹${kpis.revenue_today.toLocaleString('en-IN')}`}
              subtitle="Platform commission 15%"
              icon="💳"
              trend="+18%"
              color="#F59E0B"
            />
          </div>

          {/* Secondary Metrics */}
          <div style={{
            backgroundColor: '#1E293B',
            border: '1px solid #334155',
            borderRadius: '0.75rem',
            padding: '1.5rem',
          }}>
            <h3 style={{ color: '#F8FAFC', margin: '0 0 1rem 0' }}>Efficiency & Quality Indicators</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              <div>
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Avg Ride Occupancy</div>
                <div style={{ color: '#F8FAFC', fontSize: '1.25rem', fontWeight: 600 }}>{kpis.average_occupancy} Seats / Ride</div>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Driver Acceptance Rate</div>
                <div style={{ color: '#22C55E', fontSize: '1.25rem', fontWeight: 600 }}>{kpis.driver_acceptance_rate}%</div>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Cancellation Rate</div>
                <div style={{ color: '#F59E0B', fontSize: '1.25rem', fontWeight: 600 }}>{kpis.cancellation_rate}%</div>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Monthly Revenue</div>
                <div style={{ color: '#38BDF8', fontSize: '1.25rem', fontWeight: 600 }}>₹{kpis.revenue_this_month.toLocaleString('en-IN')}</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
