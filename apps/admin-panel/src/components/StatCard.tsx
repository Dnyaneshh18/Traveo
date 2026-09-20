import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  trend?: string;
  color?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = '#38BDF8',
}) => {
  return (
    <div style={{
      backgroundColor: '#1E293B',
      border: '1px solid #334155',
      borderRadius: '0.75rem',
      padding: '1.25rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#94A3B8', fontSize: '0.875rem', fontWeight: 500 }}>{title}</span>
        <span style={{ fontSize: '1.25rem' }}>{icon}</span>
      </div>

      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: color }}>
        {value}
      </div>

      {(subtitle || trend) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748B' }}>
          {subtitle && <span>{subtitle}</span>}
          {trend && <span style={{ color: trend.startsWith('+') ? '#22C55E' : '#EF4444' }}>{trend}</span>}
        </div>
      )}
    </div>
  );
};
