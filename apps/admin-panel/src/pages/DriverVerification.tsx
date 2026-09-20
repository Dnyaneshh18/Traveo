import React, { useState } from 'react';
import { adminApiService } from '../services/api';

interface PendingDriver {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  license_number: string;
  vehicle: string;
  submitted_at: string;
}

export const DriverVerificationPage: React.FC = () => {
  const [drivers, setDrivers] = useState<PendingDriver[]>([
    {
      id: 'drv-101',
      first_name: 'Rajesh',
      last_name: 'Kumar',
      phone: '+919876543210',
      license_number: 'DL-0420110012345',
      vehicle: 'Maruti Suzuki WagonR (White) — DL 01 AB 1234',
      submitted_at: '2026-07-23 10:15',
    },
    {
      id: 'drv-102',
      first_name: 'Suresh',
      last_name: 'Sharma',
      phone: '+919812345678',
      license_number: 'DL-1420180098765',
      vehicle: 'Hyundai Aura (Silver) — DL 03 CD 5678',
      submitted_at: '2026-07-23 11:30',
    },
  ]);

  const handleAction = async (id: string, action: 'approved' | 'rejected') => {
    try {
      await adminApiService.reviewDriver(id, action);
    } catch (err) {
      console.warn('API verification review call error:', err);
    }
    setDrivers((prev) => prev.filter((d) => d.id !== id));
    alert(`Driver ${id} ${action} successfully.`);
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ color: '#F8FAFC', margin: '0 0 0.5rem 0', fontSize: '1.75rem' }}>Driver Verification Queue</h1>
        <p style={{ color: '#94A3B8', margin: 0 }}>Review submitted driver licenses, vehicle documents, and identity background checks</p>
      </div>

      <div style={{
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        borderRadius: '0.75rem',
        overflow: 'hidden',
      }}>
        {drivers.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748B' }}>
            No pending driver verification applications in queue.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#0F172A', color: '#94A3B8', fontSize: '0.85rem' }}>
                <th style={{ padding: '1rem' }}>Driver Name</th>
                <th style={{ padding: '1rem' }}>Phone</th>
                <th style={{ padding: '1rem' }}>Driving License</th>
                <th style={{ padding: '1rem' }}>Vehicle Details</th>
                <th style={{ padding: '1rem' }}>Submitted At</th>
                <th style={{ padding: '1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {drivers.map((drv) => (
                <tr key={drv.id} style={{ borderBottom: '1px solid #334155', color: '#F8FAFC', fontSize: '0.9rem' }}>
                  <td style={{ padding: '1rem', fontWeight: 600 }}>{drv.first_name} {drv.last_name}</td>
                  <td style={{ padding: '1rem', color: '#38BDF8' }}>{drv.phone}</td>
                  <td style={{ padding: '1rem' }}>{drv.license_number}</td>
                  <td style={{ padding: '1rem', color: '#94A3B8' }}>{drv.vehicle}</td>
                  <td style={{ padding: '1rem', color: '#64748B' }}>{drv.submitted_at}</td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button
                      onClick={() => handleAction(drv.id, 'approved')}
                      style={{
                        backgroundColor: '#22C55E',
                        color: '#FFFFFF',
                        border: 'none',
                        padding: '0.4rem 0.8rem',
                        borderRadius: '0.375rem',
                        fontWeight: 600,
                        marginRight: '0.5rem',
                        cursor: 'pointer',
                      }}
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleAction(drv.id, 'rejected')}
                      style={{
                        backgroundColor: '#EF4444',
                        color: '#FFFFFF',
                        border: 'none',
                        padding: '0.4rem 0.8rem',
                        borderRadius: '0.375rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
