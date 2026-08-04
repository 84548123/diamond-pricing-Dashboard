import React from 'react';
import { StoneSellingMatch } from '../../../types/diamond';
import { X, DollarSign, TrendingUp, ShieldCheck, Scale, AlertCircle, Award, CheckCircle2 } from 'lucide-react';

interface StoneDetailModalProps {
  stone: StoneSellingMatch | null;
  isOpen: boolean;
  onClose: () => void;
}

export const StoneDetailModal: React.FC<StoneDetailModalProps> = ({ stone, isOpen, onClose }) => {
  if (!isOpen || !stone) return null;

  const isProfitable = (stone.expected_profit || 0) > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-3xl w-full p-6 shadow-2xl relative my-8 text-white">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-slate-800/50 rounded-xl hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-white/10">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl">
            <Award className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-2xl font-bold">{stone.carat.toFixed(2)} ct {stone.shape}</h2>
              <span className={`px-3 py-1 rounded-lg text-xs font-black ${
                stone.action === 'SELL NOW' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                stone.action === 'WAIT' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}>
                {stone.action}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Diamax Inventory ID: {stone.diamax_stone_id} | VDB ID: {stone.vdb_stone_id || 'N/A'}
            </p>
          </div>
        </div>

        {/* AI Executive Summary Box */}
        <div className={`p-4 rounded-xl mb-6 border ${
          isProfitable ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200' : 'bg-rose-950/30 border-rose-500/30 text-rose-200'
        }`}>
          <div className="flex items-start space-x-3">
            {isProfitable ? <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" /> : <AlertCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />}
            <div>
              <h4 className="font-bold text-sm">AI Selling Verdict</h4>
              <p className="text-xs mt-1 leading-relaxed">
                {isProfitable 
                  ? `YES! You can sell this stone profitably with an expected profit of $${stone.expected_profit?.toLocaleString()} (${stone.profit_pct?.toFixed(1)}% margin). AI Recommendation: ${stone.recommendation}.`
                  : `AVOID selling at current benchmark price. Market price does not yield acceptable profit margin.`
                }
              </p>
            </div>
          </div>
        </div>

        {/* 10 Attribute Certificate Specs */}
        <div className="mb-6">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">10 Matching Attributes</h4>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
            {[
              { label: 'Shape', val: stone.shape },
              { label: 'Carat', val: `${stone.carat.toFixed(2)} ct` },
              { label: 'Color', val: stone.color },
              { label: 'Clarity', val: stone.clarity },
              { label: 'Cut', val: stone.cut },
              { label: 'Polish', val: stone.polish },
              { label: 'Symmetry', val: stone.symmetry },
              { label: 'Fluorescence', val: stone.fluorescence },
              { label: 'Lab', val: stone.lab },
              { label: 'Country', val: stone.country },
            ].map((attr, idx) => (
              <div key={idx} className="bg-slate-800/50 p-2.5 rounded-xl border border-white/5 text-center">
                <span className="block text-[10px] text-slate-400">{attr.label}</span>
                <span className="text-xs font-bold text-slate-200">{attr.val}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Strategic Price Breakdown Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800/40 p-4 rounded-xl border border-white/5">
            <span className="text-xs text-slate-400 block">Minimum Acceptable Price</span>
            <span className="text-xl font-bold text-slate-200">${stone.min_selling_price?.toLocaleString()}</span>
            <p className="text-[10px] text-slate-500 mt-1">Floor price for break-even negotiation</p>
          </div>

          <div className="bg-emerald-500/10 p-4 rounded-xl border border-emerald-500/30">
            <span className="text-xs text-emerald-400 font-bold block">Recommended Selling Price</span>
            <span className="text-2xl font-black text-emerald-300">${stone.recommended_selling_price?.toLocaleString()}</span>
            <p className="text-[10px] text-emerald-400/80 mt-1">Optimal sweet spot for fast profitable sale</p>
          </div>

          <div className="bg-purple-500/10 p-4 rounded-xl border border-purple-500/30">
            <span className="text-xs text-purple-400 font-bold block">Premium Selling Price</span>
            <span className="text-xl font-bold text-purple-300">${stone.premium_selling_price?.toLocaleString()}</span>
            <p className="text-[10px] text-purple-400/80 mt-1">Maximum obtainable market price</p>
          </div>
          <div className="bg-yellow-500/10 p-4 rounded-xl border border-yellow-500/30">
            <span className="text-xs text-yellow-300 font-bold block">Top 1% VDB Price Target</span>
            <span className="text-xl font-black text-yellow-200">{stone.top_1pct_listing_price != null ? `$${stone.top_1pct_listing_price.toLocaleString()}` : 'Not advised'}</span>
            <p className="text-[10px] text-yellow-200/70 mt-1">{stone.top_1pct_status || 'Exact comparable required'}</p>
          </div>
        </div>

        {/* Negotiation & Profit Analysis */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-800/40 p-4 rounded-xl border border-white/5 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Diamax Inventory Cost:</span>
              <span className="font-bold text-amber-400">${stone.diamax_price?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">VDB Benchmark Price:</span>
              <span className="font-bold text-cyan-400">${stone.vdb_bottom_price?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs pt-2 border-t border-white/5">
              <span className="text-slate-400">Negotiation Range:</span>
              <span className="font-bold text-slate-200 font-mono">{stone.negotiation_range}</span>
            </div>
          </div>

          <div className="bg-slate-800/40 p-4 rounded-xl border border-white/5 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Expected Profit ($):</span>
              <span className="font-bold text-emerald-400">${stone.expected_profit?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Profit Margin (%):</span>
              <span className="font-bold text-emerald-400">{stone.profit_pct?.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between text-xs pt-2 border-t border-white/5">
              <span className="text-slate-400">Competitiveness Score:</span>
              <span className="font-bold text-brand-400">{stone.competitiveness_score}%</span>
            </div>
          </div>
        </div>

        {/* Footer close */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-brand-500 hover:bg-brand-400 text-white font-bold text-xs rounded-xl shadow-lg transition-all"
          >
            Close Intelligence View
          </button>
        </div>
      </div>
    </div>
  );
};
