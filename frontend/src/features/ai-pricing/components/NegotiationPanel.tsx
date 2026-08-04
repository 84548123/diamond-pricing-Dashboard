import React from 'react';

interface NegotiationPanelProps {
  buyPrice: number;
  maxBuyPrice: number;
  minSellPrice: number;
  recommendedSellPrice: number;
  premiumSellPrice: number;
}

export const NegotiationPanel: React.FC<NegotiationPanelProps> = ({
  buyPrice, maxBuyPrice, minSellPrice, recommendedSellPrice, premiumSellPrice
}) => {
  const min = buyPrice;
  const max = premiumSellPrice;
  const range = max - min;

  const getPosition = (val: number) => `${((val - min) / range) * 100}%`;

  return (
    <div className="w-full pt-6 pb-8 px-4">
      <div className="relative h-3 w-full rounded-full bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-500">
        <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)] border-2 border-dark-950" style={{ left: '0%' }}>
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-slate-400 font-medium">Buy: ${buyPrice}</div>
        </div>
        
        <div className="absolute top-1/2 -translate-y-1/2 w-2 h-4 bg-dark-900 border border-white/20" style={{ left: getPosition(maxBuyPrice) }}>
          <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-slate-300 font-medium">Max Buy: ${maxBuyPrice}</div>
        </div>

        <div className="absolute top-1/2 -translate-y-1/2 w-2 h-4 bg-dark-900 border border-white/20" style={{ left: getPosition(minSellPrice) }}>
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-slate-300 font-medium">Min Sell: ${minSellPrice}</div>
        </div>

        <div className="absolute top-1/2 -translate-y-1/2 w-2 h-4 bg-dark-900 border border-white/20" style={{ left: getPosition(recommendedSellPrice) }}>
          <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-brand-400 font-bold">Rec Sell: ${recommendedSellPrice}</div>
        </div>

        <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)] border-2 border-dark-950" style={{ left: '100%' }}>
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-emerald-400 font-bold">Prem: ${premiumSellPrice}</div>
        </div>
      </div>
    </div>
  );
};
