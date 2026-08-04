import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ProfitChartProps {
  data: any[];
}

export const ProfitChart: React.FC<ProfitChartProps> = ({ data }) => {
  const getColor = (tier: string) => {
    switch(tier) {
      case 'STRONG_BUY': return '#34d399';
      case 'BUY': return '#60a5fa';
      case 'HOLD': return '#fbbf24';
      case 'WAIT': return '#f97316';
      case 'AVOID': return '#fb7185';
      default: return '#94a3b8';
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 !bg-dark-900/90 border-white/10">
          <p className="text-xs text-slate-400 mb-1">{label}</p>
          <p className="text-sm font-bold text-white" style={{ color: payload[0].fill }}>
            {payload[0].value}% Profit
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}%`} />
          <Tooltip content={<CustomTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} />} />
          <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.tier)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
