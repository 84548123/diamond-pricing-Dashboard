import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const ColorAnalysis = () => {
  const data = [
    { grade: 'D', count: 150, profit: 12 },
    { grade: 'E', count: 200, profit: 14 },
    { grade: 'F', count: 280, profit: 16 },
    { grade: 'G', count: 320, profit: 18 },
    { grade: 'H', count: 250, profit: 20 },
    { grade: 'I', count: 180, profit: 22 },
    { grade: 'J', count: 100, profit: 24 },
    { grade: 'K-M', count: 50, profit: 26 },
  ];

  const getColor = (index: number) => {
    const colors = ['#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b', '#475569', '#334155'];
    return colors[index % colors.length];
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-2">Color Grade Distribution</h2>
        <p className="text-slate-400 mb-8">Analysis of inventory and average profit margin grouped by color grades.</p>
        
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="grade" stroke="#64748b" />
              <YAxis yAxisId="left" stroke="#64748b" />
              <YAxis yAxisId="right" orientation="right" stroke="#64748b" tickFormatter={(val) => `${val}%`} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
              />
              <Bar yAxisId="left" dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
