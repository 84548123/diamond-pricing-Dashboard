import React from 'react';
import { useFilterStore } from '../../store/filterStore';
import { RotateCcw } from 'lucide-react';

export const FilterPanel = () => {
  const filters = useFilterStore();

  const shapes = ['ALL', 'ROUND', 'OVAL', 'EMERALD', 'CUSHION', 'PRINCESS', 'PEAR', 'RADIANT', 'MARQUISE', 'HEART', 'ASSCHER'];
  const colors = ['ALL', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'];
  const clarities = ['ALL', 'FL', 'IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'SI3', 'I1', 'I2', 'I3'];
  const recommendations = ['ALL', 'STRONG_BUY', 'BUY', 'HOLD', 'WAIT', 'AVOID'];
  const sortOptions = [
    { value: 'profit_margin_pct', label: 'Profit % (High to Low)' },
    { value: 'confidence_score', label: 'Confidence (High to Low)' },
    { value: 'carat', label: 'Carat (High to Low)' },
    { value: 'expected_profit', label: 'Expected Profit ($)' }
  ];

  return (
    <div className="glass-card p-4 mb-6 flex flex-wrap items-center gap-4">
      <div className="flex-1 min-w-[120px]">
        <label className="block text-xs font-medium text-slate-400 mb-1">Shape</label>
        <select 
          value={filters.shape} 
          onChange={(e) => filters.setFilter('shape', e.target.value === 'ALL' ? '' : e.target.value)}
          className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
        >
          {shapes.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="flex-1 min-w-[100px]">
        <label className="block text-xs font-medium text-slate-400 mb-1">Color</label>
        <select 
          value={filters.color} 
          onChange={(e) => filters.setFilter('color', e.target.value === 'ALL' ? '' : e.target.value)}
          className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
        >
          {colors.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="flex-1 min-w-[100px]">
        <label className="block text-xs font-medium text-slate-400 mb-1">Clarity</label>
        <select 
          value={filters.clarity} 
          onChange={(e) => filters.setFilter('clarity', e.target.value === 'ALL' ? '' : e.target.value)}
          className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
        >
          {clarities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="flex-1 min-w-[140px]">
        <label className="block text-xs font-medium text-slate-400 mb-1">Recommendation</label>
        <select 
          value={filters.recommendation} 
          onChange={(e) => filters.setFilter('recommendation', e.target.value === 'ALL' ? '' : e.target.value)}
          className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
        >
          {recommendations.map(r => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
        </select>
      </div>

      <div className="flex-1 min-w-[180px] flex space-x-2">
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-400 mb-1">Min Profit %</label>
          <input 
            type="number" 
            placeholder="0"
            value={filters.minProfit} 
            onChange={(e) => filters.setFilter('minProfit', e.target.value)}
            className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-400 mb-1">Max Profit %</label>
          <input 
            type="number" 
            placeholder="100"
            value={filters.maxProfit} 
            onChange={(e) => filters.setFilter('maxProfit', e.target.value)}
            className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
          />
        </div>
      </div>

      <div className="flex-1 min-w-[180px]">
        <label className="block text-xs font-medium text-slate-400 mb-1">Sort By</label>
        <select 
          value={filters.sortBy} 
          onChange={(e) => filters.setFilter('sortBy', e.target.value)}
          className="w-full bg-dark-900/50 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-brand-500/50 transition-colors"
        >
          {sortOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      <div className="flex items-end pb-0.5">
        <button 
          onClick={filters.resetFilters}
          className="p-2 bg-dark-800 hover:bg-dark-700 border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors"
          title="Reset Filters"
        >
          <RotateCcw className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
