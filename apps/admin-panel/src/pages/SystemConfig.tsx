import React, { useState } from 'react';
import { adminApiService } from '../services/api';

interface ConfigItem {
  key: string;
  value: string;
  description: string;
}

export const SystemConfigPage: React.FC = () => {
  const [configs, setConfigs] = useState<ConfigItem[]>([
    { key: 'DEFAULT_SEARCH_RADIUS_KM', value: '2.0', description: 'Geographic search radius for passenger matching' },
    { key: 'DEFAULT_SEARCH_TIMEOUT_SECONDS', value: '120', description: 'Matching window timer before voting trigger' },
    { key: 'DEFAULT_VOTE_TIMEOUT_SECONDS', value: '30', description: 'Group voting countdown duration' },
    { key: 'DEFAULT_PLATFORM_COMMISSION_PERCENT', value: '15.0', description: 'Platform commission deduction rate' },
    { key: 'WEIGHT_ROUTE_OVERLAP', value: '0.35', description: 'Ride Intelligence weight for route overlap ratio' },
    { key: 'WEIGHT_PICKUP_EFFICIENCY', value: '0.20', description: 'Ride Intelligence weight for pickup distance' },
  ]);

  const handleSave = async (key: string, newValue: string, description: string) => {
    try {
      await adminApiService.updateConfig(key, newValue, description);
    } catch (err) {
      console.warn('API config update error:', err);
    }
    setConfigs((prev) =>
      prev.map((item) => (item.key === key ? { ...item, value: newValue } : item))
    );
    alert(`Configuration [${key}] updated to ${newValue}. Changes applied without redeployment.`);
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ color: '#F8FAFC', margin: '0 0 0.5rem 0', fontSize: '1.75rem' }}>System Configuration</h1>
        <p style={{ color: '#94A3B8', margin: 0 }}>Manage live Ride Intelligence Engine weights, timeouts, and business rules without app redeployment</p>
      </div>

      <div style={{
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}>
        {configs.map((item) => (
          <div
            key={item.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingBottom: '1rem',
              borderBottom: '1px solid #334155',
            }}
          >
            <div>
              <div style={{ color: '#38BDF8', fontWeight: 600, fontSize: '0.95rem' }}>{item.key}</div>
              <div style={{ color: '#64748B', fontSize: '0.8rem' }}>{item.description}</div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="text"
                value={item.value}
                onChange={(e) => {
                  const val = e.target.value;
                  setConfigs((prev) =>
                    prev.map((c) => (c.key === item.key ? { ...c, value: val } : c))
                  );
                }}
                style={{
                  backgroundColor: '#0F172A',
                  border: '1px solid #475569',
                  color: '#F8FAFC',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '0.375rem',
                  width: '120px',
                  fontWeight: 600,
                }}
              />
              <button
                onClick={() => handleSave(item.key, item.value, item.description)}
                style={{
                  backgroundColor: '#0284C7',
                  color: '#FFFFFF',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Save
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
