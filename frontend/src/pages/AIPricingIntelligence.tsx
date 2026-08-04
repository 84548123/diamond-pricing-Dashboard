import React, { useState, useEffect, useCallback } from 'react';
import { Diamond, Rocket, TrendingUp, DollarSign, Sliders, FileSpreadsheet, FileText, RefreshCw, Zap, Search, ChevronLeft, ChevronRight, Grid, List } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { PriceComparisonGrid } from '../features/ai-pricing/components/PriceComparisonGrid';
import { SellingRulesModal } from '../features/ai-pricing/components/SellingRulesModal';
import { StoneDetailModal } from '../features/ai-pricing/components/StoneDetailModal';
import { CaratMatrixView } from '../features/ai-pricing/components/CaratMatrixView';
import { StoneSellingMatch, SellingSummary, RuleConfig } from '../types/diamond';
import { getSellingIntelligence, getRules, updateRules, downloadExcelReport, downloadPdfReport, generateSampleData } from '../api/client';
import { Spinner } from '../components/ui/Spinner';

export const AIPricingIntelligence: React.FC = () => {
  const [activeViewTab, setActiveViewTab] = useState<'grid' | 'matrix'>('grid');

  const [data, setData] = useState<StoneSellingMatch[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [summary, setSummary] = useState<SellingSummary | null>(null);
  const [rules, setRules] = useState<RuleConfig | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(50);
  const [search, setSearch] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('');
  const [shapeFilter, setShapeFilter] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [isRulesModalOpen, setIsRulesModalOpen] = useState<boolean>(false);
  const [selectedStone, setSelectedStone] = useState<StoneSellingMatch | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { page, page_size: pageSize };
      if (search) params.search = search;
      if (actionFilter) params.action = actionFilter;
      if (shapeFilter) params.shape = shapeFilter;

      const [intelRes, rulesRes] = await Promise.all([
        getSellingIntelligence(params),
        getRules()
      ]);

      setData(intelRes.items || []);
      setTotal(intelRes.total || 0);
      setSummary(intelRes.summary || null);
      setRules(rulesRes);
    } catch (err: any) {
      console.error('Failed to load selling intelligence data:', err);
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, actionFilter, shapeFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerateScaleSample = async () => {
    setGenerating(true);
    try {
      await generateSampleData(1500000, 40000);
      setPage(1);
      await loadData();
    } catch (err: any) {
      console.error('Scale dataset generation failed:', err);
      alert('Failed to generate scale datasets: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveRules = async (newRules: RuleConfig) => {
    try {
      const res = await updateRules(newRules);
      setRules(res.config);
      setSummary(res.summary);
      await loadData();
    } catch (err) {
      console.error('Failed to update selling rules:', err);
    }
  };

  return (
    <div className="flex flex-col h-full animate-fade-in p-6 bg-slate-950 min-h-screen text-white">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 gap-4 pb-4 border-b border-white/10">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-r from-brand-500 to-emerald-400 rounded-xl text-slate-950 font-black">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                AI Diamond Selling Intelligence Dashboard
              </h1>
              <p className="text-xs text-slate-400">
                Live inventory engine • current inventory, historical sales, exact VDB, EV, and staged minimum-loss pricing
              </p>
            </div>
          </div>
        </div>

        {/* View Mode Tab Switcher & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Main View Mode Tabs */}
          <div className="flex items-center p-1 bg-slate-900 rounded-xl border border-white/10">
            <button
              onClick={() => setActiveViewTab('grid')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeViewTab === 'grid' ? 'bg-brand-500 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              <List className="w-4 h-4" />
              <span>Grid Intelligence View</span>
            </button>
            <button
              onClick={() => setActiveViewTab('matrix')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeViewTab === 'matrix' ? 'bg-brand-500 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Grid className="w-4 h-4" />
              <span>Carat Bin Matrix View</span>
            </button>
          </div>

          <button
            onClick={handleGenerateScaleSample}
            disabled={generating}
            className="flex items-center space-x-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Generating...' : 'Generate 15 Lakh Test Dataset'}</span>
          </button>

          <button
            onClick={() => setIsRulesModalOpen(true)}
            className="flex items-center space-x-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-white/10 text-slate-200 text-xs font-semibold rounded-xl transition-all"
          >
            <Sliders className="w-3.5 h-3.5 text-brand-400" />
            <span>Rules</span>
          </button>

          <button
            onClick={downloadExcelReport}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-white/10 text-emerald-400 text-xs font-semibold rounded-xl transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Excel</span>
          </button>

          <button
            onClick={downloadPdfReport}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-white/10 text-rose-400 text-xs font-semibold rounded-xl transition-all"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>PDF</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-5 mb-6">
        <Card title="Live excess-stock stones" value={summary?.total_matches ? summary.total_matches.toLocaleString() : '0'} icon={Diamond} gradient="from-brand-500 to-accent-cyan" trend={summary?.match_rate} trendLabel="of inventory" />
        <Card title="Staged reductions" value={summary?.sell_now_count ? summary.sell_now_count.toLocaleString() : '0'} icon={Rocket} gradient="from-emerald-500 to-emerald-300" />
        <Card title="Average rate move" value={`${summary?.avg_profit_margin?.toFixed(1) || 0}%`} icon={TrendingUp} gradient="from-cyan-500 to-blue-500" />
        <Card title="Live rate delta" value={`$${summary?.total_expected_profit ? summary.total_expected_profit.toLocaleString(undefined, {maximumFractionDigits:0}) : '0'}`} icon={DollarSign} gradient="from-amber-500 to-orange-400" />
        <Card title="Average sales %" value={`${summary?.avg_competitiveness?.toFixed(1) || 0}%`} icon={Zap} gradient="from-purple-500 to-pink-500" />
      </div>

      {/* Render Active View Tab */}
      {activeViewTab === 'matrix' ? (
        <CaratMatrixView />
      ) : (
        <>
          {/* Filter and Search Bar */}
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/60 p-4 rounded-xl border border-white/5 mb-4">
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search Stone ID, Shape, Lab, Country..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  className="w-full pl-9 pr-4 py-2 bg-slate-800/80 border border-white/10 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-brand-500"
                />
              </div>

              <select
                value={actionFilter}
                onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                className="px-3 py-2 bg-slate-800/80 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="">All Actions</option>
                <option value="REDUCE">Reduce price</option>
                <option value="INCREASE">Increase price</option>
                <option value="HOLD">Hold price</option>
              </select>

              <select
                value={shapeFilter}
                onChange={(e) => { setShapeFilter(e.target.value); setPage(1); }}
                className="px-3 py-2 bg-slate-800/80 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="">All Shapes</option>
                <option value="ROUND">ROUND</option>
                <option value="OVAL">OVAL</option>
                <option value="PRINCESS">PRINCESS</option>
                <option value="CUSHION">CUSHION</option>
                <option value="EMERALD">EMERALD</option>
                <option value="PEAR">PEAR</option>
                <option value="MARQUISE">MARQUISE</option>
                <option value="RADIANT">RADIANT</option>
              </select>
            </div>

            <div className="text-xs text-slate-400 font-mono">
              Showing {data.length} of {total.toLocaleString()} stone records
            </div>
          </div>

          {/* Main Grid View */}
          <div className="relative min-h-[500px]">
            {loading && (
              <div className="absolute inset-0 z-10 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center rounded-xl">
                <Spinner size="lg" />
                <span className="text-xs text-slate-400 mt-3 font-semibold">Processing Polars intelligence query...</span>
              </div>
            )}

            {error ? (
              <div className="p-8 text-center bg-rose-950/20 border border-rose-500/30 rounded-xl text-rose-300">
                {error}
              </div>
            ) : data.length === 0 && !loading ? (
              <div className="p-12 text-center bg-slate-900/50 border border-white/5 rounded-xl text-slate-400">
                <p className="text-sm font-semibold mb-2">No matched stones found for selected filters.</p>
                <p className="text-xs text-slate-500">Import VDB & Diamax files or click "Generate 15 Lakh Test Dataset" above.</p>
              </div>
            ) : (
              <PriceComparisonGrid data={data} onRowClick={(stone) => setSelectedStone(stone)} />
            )}
          </div>

          {/* Server Pagination */}
          <div className="mt-4 flex flex-col sm:flex-row justify-between items-center bg-slate-900/60 p-4 rounded-xl border border-white/5 gap-3">
            <div className="text-xs text-slate-400">
              Page <span className="font-bold text-white">{page}</span> of <span className="font-bold text-white">{Math.max(1, Math.ceil(total / pageSize))}</span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs font-semibold text-slate-200 border border-white/10"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Previous</span>
              </button>

              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage(p => p + 1)}
                className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs font-semibold text-slate-200 border border-white/10"
              >
                <span>Next</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Selling Rules Modal */}
      <SellingRulesModal
        isOpen={isRulesModalOpen}
        onClose={() => setIsRulesModalOpen(false)}
        config={rules}
        onSave={handleSaveRules}
      />

      {/* Stone Detail Modal */}
      <StoneDetailModal
        stone={selectedStone}
        isOpen={!!selectedStone}
        onClose={() => setSelectedStone(null)}
      />
    </div>
  );
};
