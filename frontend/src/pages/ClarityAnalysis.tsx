import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const ClarityAnalysis = () => {
  const data = [
    { grade: 'FL/IF', count: 80, profit: 10 },
    { grade: 'VVS1', count: 120, profit: 12 },
    { grade: 'VVS2', count: 180, profit: 14 },
    { grade: 'VS1', count: 250, profit: 16 },
    { grade: 'VS2', count: 350, profit: 18 },
    { grade: 'SI1', count: 400, profit: 22 },
    { grade: 'SI2', count: 200, profit: 25 },
    { grade: 'I1-I3', count: 50, profit: 28 },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-2">Clarity Grade Distribution</h2>
        <p className="text-slate-400 mb-8">Analysis of inventory and average profit margin grouped by clarity grades.</p>
        
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
              <Bar yAxisId="left" dataKey="count" name="Count" fill="#22d3ee" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
