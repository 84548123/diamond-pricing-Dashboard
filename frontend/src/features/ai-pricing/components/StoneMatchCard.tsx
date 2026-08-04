import React from 'react';
import { TrendingUp, Gem } from 'lucide-react';
import { StoneSellingMatch } from '../../../types/diamond';

interface StoneMatchCardProps {
  stone: StoneSellingMatch;
  onClick: () => void;
}

export const StoneMatchCard: React.FC<StoneMatchCardProps> = ({ stone, onClick }) => {
  const isPositive = stone.expected_profit > 0;

  return (
    <div 
      className="bg-slate-900 rounded-xl p-4 border border-white/10 flex flex-col group cursor-pointer hover:border-brand-500/30 transition-all duration-300 transform hover:-translate-y-1 relative overflow-hidden"
      onClick={onClick}
    >
      <div className="flex justify-between items-center bg-slate-950/40 p-3 rounded-lg border border-white/5 mb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-slate-800 rounded-lg border border-white/10">
            <Gem className="w-5 h-5 text-brand-400" />
          </div>
          <div>
            <div className="font-bold text-base text-white">
              {stone.carat}ct {stone.shape}
            </div>
            <div className="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
              <span className="font-medium text-slate-300">{stone.color}</span>
              <span>•</span>
              <span className="font-medium text-slate-300">{stone.clarity}</span>
              <span>•</span>
              <span>{stone.cut}/{stone.polish}/{stone.symmetry}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-white/5">
          <div className="text-[10px] text-slate-400 uppercase font-bold">VDB Market</div>
          <div className="text-sm font-bold text-emerald-400">${stone.vdb_bottom_price ? stone.vdb_bottom_price.toLocaleString() : 'N/A'}</div>
        </div>
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-white/5">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Our Inventory</div>
          <div className="text-sm font-bold text-amber-400">${stone.diamax_price.toLocaleString()}</div>
        </div>
      </div>

      <div className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-white/5">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <span className="text-xs text-slate-300 font-semibold">AI Recommended</span>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold text-cyan-300">
            ${stone.recommended_selling_price ? stone.recommended_selling_price.toLocaleString() : 'N/A'}
          </div>
          <div className="text-[10px] font-bold text-emerald-400">
            +{stone.profit_pct}%
          </div>
        </div>
      </div>
    </div>
  );
};
