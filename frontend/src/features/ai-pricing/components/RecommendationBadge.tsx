import React from 'react';
import { Rocket, ThumbsUp, PauseCircle, Clock, XCircle } from 'lucide-react';
import { Recommendation } from '../../../types/diamond';
import { StarRating } from '../../../components/ui/StarRating';

export const RecommendationBadge: React.FC<{ recommendation: Recommendation, stars: number }> = ({ recommendation, stars }) => {
  const config = {
    STRONG_BUY: { icon: Rocket, color: 'emerald', bg: 'from-emerald-500/20 to-emerald-400/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'STRONG BUY' },
    BUY: { icon: ThumbsUp, color: 'blue', bg: 'from-blue-500/20 to-blue-400/10', border: 'border-blue-500/30', text: 'text-blue-400', label: 'BUY' },
    HOLD: { icon: PauseCircle, color: 'amber', bg: 'from-amber-500/20 to-amber-400/10', border: 'border-amber-500/30', text: 'text-amber-400', label: 'HOLD' },
    WAIT: { icon: Clock, color: 'orange', bg: 'from-orange-500/20 to-orange-400/10', border: 'border-orange-500/30', text: 'text-orange-400', label: 'WAIT' },
    AVOID: { icon: XCircle, color: 'rose', bg: 'from-rose-500/20 to-rose-400/10', border: 'border-rose-500/30', text: 'text-rose-400', label: 'AVOID' }
  };

  const current = config[recommendation] || config.HOLD;
  const Icon = current.icon;
  const isStrong = recommendation === 'STRONG_BUY';

  return (
    <div className={`w-full flex flex-col items-center justify-center p-3 rounded-xl border ${current.border} bg-gradient-to-br ${current.bg} ${isStrong ? 'animate-[pulse_3s_ease-in-out_infinite]' : ''}`}>
      <div className="flex items-center space-x-2 mb-1">
        <Icon className={`w-5 h-5 ${current.text}`} />
        <span className={`font-bold tracking-wider ${current.text}`}>{current.label}</span>
      </div>
      <StarRating rating={stars} max={5} />
    </div>
  );
};
