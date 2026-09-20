import React from 'react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'rides', label: 'Live Rides', icon: '🚕' },
    { id: 'verification', label: 'Driver Verification', icon: '🛡️' },
    { id: 'passengers', label: 'Passengers', icon: '👥' },
    { id: 'drivers', label: 'Drivers', icon: '🚘' },
    { id: 'configuration', label: 'System Setup', icon: '⚙️' },
    { id: 'audit', label: 'Audit Logs', icon: '📜' },
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: '#1E293B',
      borderRight: '1px solid #334155',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem 1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0 0.5rem 1.5rem 0.5rem' }}>
        <span style={{ fontSize: '1.75rem' }}>🚖</span>
        <div>
          <h2 style={{ color: '#38BDF8', margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Traveo</h2>
          <span style={{ color: '#64748B', fontSize: '0.75rem' }}>Operations Control</span>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {menuItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: '0.5rem',
                border: 'none',
                backgroundColor: isActive ? '#0284C7' : 'transparent',
                color: isActive ? '#FFFFFF' : '#94A3B8',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};
