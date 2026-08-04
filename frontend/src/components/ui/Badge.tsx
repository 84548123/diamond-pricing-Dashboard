import React from 'react';
import { Recommendation } from '../../types/diamond';

interface BadgeProps {
  recommendation: Recommendation | string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Badge: React.FC<BadgeProps> = ({ recommendation, className = '', size = 'md' }) => {
  const getStyles = (rec: string) => {
    switch (rec) {
      case 'STRONG_BUY': return 'bg-accent-emerald/15 text-accent-emerald border-accent-emerald/30 shadow-[0_0_10px_rgba(52,211,153,0.2)]';
      case 'BUY': return 'bg-blue-500/15 text-blue-400 border-blue-500/30 shadow-[0_0_10px_rgba(96,165,250,0.2)]';
      case 'HOLD': return 'bg-accent-amber/15 text-accent-amber border-accent-amber/30 shadow-[0_0_10px_rgba(251,191,36,0.2)]';
      case 'WAIT': return 'bg-orange-500/15 text-orange-400 border-orange-500/30 shadow-[0_0_10px_rgba(249,115,22,0.2)]';
      case 'AVOID': return 'bg-accent-rose/15 text-accent-rose border-accent-rose/30 shadow-[0_0_10px_rgba(251,113,133,0.2)]';
      default: return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    }
  };

  const getLabel = (rec: string) => rec.replace('_', ' ');

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5',
    md: 'text-xs px-2 py-1',
    lg: 'text-sm px-3 py-1.5'
  };

  return (
    <span className={`inline-flex items-center justify-center font-semibold rounded border uppercase tracking-wider ${getStyles(recommendation)} ${sizeClasses[size]} ${className}`}>
      {getLabel(recommendation)}
    </span>
  );
};
