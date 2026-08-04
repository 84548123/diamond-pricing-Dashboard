import React, { useState, useEffect } from 'react';
import { RuleConfig } from '../../../types/diamond';
import { Settings, Sliders, Check, RefreshCw } from 'lucide-react';

interface SellingRulesModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: RuleConfig | null;
  onSave: (newRules: RuleConfig) => Promise<void>;
}

export const SellingRulesModal: React.FC<SellingRulesModalProps> = ({
  isOpen,
  onClose,
  config,
  onSave
}) => {
  const [rules, setRules] = useState<RuleConfig>({
    premium_threshold: 15.0,
    sell_now_threshold: 10.0,
    good_opp_threshold: 5.0,
    wait_threshold: 3.0
  });

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (config) {
      setRules(config);
    }
  }, [config]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(rules);
      onClose();
    } catch (err) {
      console.error('Failed to update rules:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-white/10">
          <div className="p-2.5 bg-brand-500/20 text-brand-400 rounded-xl">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Configurable Smart Selling Rules</h3>
            <p className="text-xs text-slate-400">Adjust market difference thresholds to customize AI recommendations</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
              <span>PREMIUM SELL OPPORTUNITY (★★★★★)</span>
              <span className="text-purple-400 font-bold">≥ {rules.premium_threshold}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="30"
              step="0.5"
              value={rules.premium_threshold}
              onChange={(e) => setRules({ ...rules, premium_threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
            <span className="text-[11px] text-slate-500">Stones with market difference equal or above this % trigger Premium Selling</span>
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
              <span>SELL NOW (★★★★☆)</span>
              <span className="text-emerald-400 font-bold">{rules.sell_now_threshold}% - {rules.premium_threshold}%</span>
            </div>
            <input
              type="range"
              min="5"
              max="20"
              step="0.5"
              value={rules.sell_now_threshold}
              onChange={(e) => setRules({ ...rules, sell_now_threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
              <span>GOOD SELLING OPPORTUNITY (★★★☆☆)</span>
              <span className="text-cyan-400 font-bold">{rules.good_opp_threshold}% - {rules.sell_now_threshold}%</span>
            </div>
            <input
              type="range"
              min="3"
              max="12"
              step="0.5"
              value={rules.good_opp_threshold}
              onChange={(e) => setRules({ ...rules, good_opp_threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
              <span>WAIT (★★☆☆☆)</span>
              <span className="text-amber-400 font-bold">{rules.wait_threshold}% - {rules.good_opp_threshold}%</span>
            </div>
            <input
              type="range"
              min="1"
              max="8"
              step="0.5"
              value={rules.wait_threshold}
              onChange={(e) => setRules({ ...rules, wait_threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <span className="text-[11px] text-slate-500">Stones below {rules.wait_threshold}% market difference will be recommended as AVOID</span>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center space-x-2 px-5 py-2 bg-brand-500 hover:bg-brand-400 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-500/30 transition-all"
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              <span>Apply & Recalculate AI Intelligence</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
