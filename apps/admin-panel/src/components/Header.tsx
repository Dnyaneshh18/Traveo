import React from 'react';

export const Header: React.FC = () => {
  return (
    <header style={{
      height: '64px',
      backgroundColor: '#1E293B',
      borderBottom: '1px solid #334155',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: '#22C55E',
          display: 'inline-block',
        }} />
        <span style={{ color: '#F8FAFC', fontSize: '0.875rem', fontWeight: 500 }}>
          System Operational — Live WebSocket Connected
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: '#F8FAFC', fontSize: '0.875rem', fontWeight: 600 }}>Super Admin</div>
          <div style={{ color: '#64748B', fontSize: '0.75rem' }}>operations@traveo.com</div>
        </div>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: '#0284C7',
          color: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          fontSize: '0.9rem',
        }}>
          SA
        </div>
      </div>
    </header>
  );
};
