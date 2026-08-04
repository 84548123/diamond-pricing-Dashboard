import React, { useState } from 'react';
import { LeaderboardsData, StoneSellingMatch } from '../../../types/diamond';
import { Trophy, Rocket, Crown, TrendingUp, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

interface LeaderboardsWidgetProps {
  data: LeaderboardsData | null;
  onSelectStone: (stone: StoneSellingMatch) => void;
}

type TabType = 'profitable' | 'sell_now' | 'premium' | 'margin' | 'wait' | 'lowest_margin';

export const LeaderboardsWidget: React.FC<LeaderboardsWidgetProps> = ({ data, onSelectStone }) => {
  const [activeTab, setActiveTab] = useState<TabType>('sell_now');

  if (!data) return null;

  const tabs = [
    { id: 'sell_now', label: 'Top SELL NOW', icon: Rocket, color: 'text-emerald-400', items: data.top_sell_now },
    { id: 'profitable', label: 'Most Profitable ($)', icon: Trophy, color: 'text-amber-400', items: data.top_profitable },
    { id: 'premium', label: 'Premium Opportunities', icon: Crown, color: 'text-purple-400', items: data.top_premium_opps },
    { id: 'margin', label: 'Highest Margin (%)', icon: TrendingUp, color: 'text-cyan-400', items: data.top_margin },
    { id: 'wait', label: 'Top WAIT', icon: Clock, color: 'text-amber-400', items: data.top_wait },
    { id: 'lowest_margin', label: 'Lowest Margin', icon: AlertTriangle, color: 'text-rose-400', items: data.lowest_margin },
  ];

  const currentTab = tabs.find(t => t.id === activeTab) || tabs[0];

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-8 shadow-xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-400" />
            AI Top 10 Selling Intelligence Leaderboards
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Curated high-precision recommendations to maximize profitability and sales velocity
          </p>
        </div>

        {/* Tabs navigation */}
        <div className="flex flex-wrap gap-2 bg-slate-950/60 p-1.5 rounded-xl border border-white/5">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive 
                    ? 'bg-slate-800 text-white shadow-md border border-white/10' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${tab.color}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Leaderboard Table / Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {currentTab.items.length === 0 ? (
          <div className="col-span-full py-8 text-center text-slate-500 text-sm">
            No stone recommendations available for this leaderboard view.
          </div>
        ) : (
          currentTab.items.map((stone, idx) => (
            <div
              key={stone.diamax_stone_id + idx}
              onClick={() => onSelectStone(stone)}
              className="bg-slate-800/40 hover:bg-slate-800 border border-white/5 hover:border-brand-500/40 p-3.5 rounded-xl cursor-pointer transition-all duration-200 group flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold font-mono text-slate-400 group-hover:text-brand-400">
                    #{idx + 1} {stone.diamax_stone_id}
                  </span>
                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded ${
                    stone.action === 'SELL NOW' ? 'bg-emerald-500/20 text-emerald-400' :
                    stone.action === 'WAIT' ? 'bg-amber-500/20 text-amber-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {stone.action}
                  </span>
                </div>

                <div className="text-sm font-semibold text-white mb-1">
                  {stone.carat.toFixed(2)} ct {stone.shape} {stone.color}/{stone.clarity}
                </div>
                <div className="text-[11px] text-slate-400 mb-3">
                  {stone.lab} • {stone.country}
                </div>
              </div>

              <div className="pt-2 border-t border-white/5 space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Rec Sell:</span>
                  <span className="font-bold text-emerald-400">${stone.recommended_selling_price?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Expected Profit:</span>
                  <span className="font-bold text-amber-400">${stone.expected_profit?.toLocaleString()} ({stone.profit_pct?.toFixed(1)}%)</span>
                </div>
                <div className="flex items-center justify-end text-[10px] text-brand-400 pt-1 group-hover:translate-x-1 transition-transform">
                  View Detail <ArrowRight className="w-3 h-3 ml-1" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
