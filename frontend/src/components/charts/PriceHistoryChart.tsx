import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface PriceHistoryChartProps {
  data: any[];
  onPeriodChange?: (period: string) => void;
}

export const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({ data, onPeriodChange }) => {
  const [period, setPeriod] = useState('24h');

  const handlePeriodChange = (p: string) => {
    setPeriod(p);
    if (onPeriodChange) onPeriodChange(p);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 !bg-dark-900/90 border-white/10">
          <p className="text-xs text-slate-400 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between space-x-4 mb-1">
              <span className="flex items-center text-sm font-medium" style={{ color: entry.color }}>
                <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: entry.color }}></span>
                {entry.name}
              </span>
              <span className="text-sm font-bold text-white">${entry.value.toLocaleString()}</span>
            </div>
          ))}
          <div className="mt-2 pt-2 border-t border-white/10 flex justify-between">
            <span className="text-xs text-slate-400">Profit Margin</span>
            <span className="text-xs font-bold text-accent-emerald">
              {payload[0].payload.profit_margin_pct}%
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-end space-x-2 mb-4">
        {['1H', '24H', '7D', '30D'].map(p => (
          <button
            key={p}
            onClick={() => handlePeriodChange(p.toLowerCase())}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${period === p.toLowerCase() ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30' : 'bg-dark-800 text-slate-400 hover:text-white border border-white/5'}`}
          >
            {p}
          </button>
        ))}
      </div>
      
      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorVdb" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorDiamax" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#fbbf24" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="recorded_at" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} />
            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="vdb_price" name="VDB Price" stroke="#22d3ee" strokeWidth={2} fillOpacity={1} fill="url(#colorVdb)" />
            <Area type="monotone" dataKey="diamax_price" name="Diamax Price" stroke="#fbbf24" strokeWidth={2} fillOpacity={1} fill="url(#colorDiamax)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
