import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface CardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: number;
  trendLabel?: string;
  gradient?: string;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, value, icon: Icon, trend, trendLabel, gradient = 'from-brand-500 to-accent-cyan', className = '' }) => {
  const isPositive = trend && trend > 0;
  const isNegative = trend && trend < 0;

  return (
    <div className={`glass-card p-6 relative overflow-hidden group hover:border-white/10 transition-all duration-300 ${className}`}>
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${gradient} opacity-5 rounded-bl-full group-hover:opacity-10 transition-opacity`}></div>
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <h3 className="text-slate-400 font-medium text-sm">{title}</h3>
        <div className={`p-2 rounded-lg bg-gradient-to-br ${gradient} bg-opacity-10 shadow-[0_0_15px_rgba(0,0,0,0.2)]`}>
          <Icon className="w-5 h-5 text-white drop-shadow-md" />
        </div>
      </div>
      
      <div className="relative z-10">
        <div className="text-3xl font-bold text-white mb-1 tracking-tight">{value}</div>
        
        {trend !== undefined && (
          <div className="flex items-center text-xs mt-2">
            <span className={`flex items-center font-medium px-1.5 py-0.5 rounded ${isPositive ? 'text-accent-emerald bg-accent-emerald/10' : isNegative ? 'text-accent-rose bg-accent-rose/10' : 'text-slate-400 bg-slate-400/10'}`}>
              {isPositive ? <ArrowUpRight className="w-3 h-3 mr-1" /> : isNegative ? <ArrowDownRight className="w-3 h-3 mr-1" /> : null}
              {Math.abs(trend)}%
            </span>
            {trendLabel && <span className="text-slate-500 ml-2">{trendLabel}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
