import React, { useEffect, useState } from 'react';
import { ArrowRight, BarChart3, CheckCircle2, CircleAlert, Database, Gem, Rocket, Upload } from 'lucide-react';
import { getImportStatus, ImportStatus } from '../api/client';
import { Spinner } from '../components/ui/Spinner';
import { useNavigate } from 'react-router-dom';

const number = (value: number) => value.toLocaleString();

export const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<ImportStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const navigate = useNavigate();
  const loadDashboard = () => {
    setLoading(true); setLoadError(false);
    getImportStatus().then(setStatus).catch(() => setLoadError(true)).finally(() => setLoading(false));
  };
  useEffect(() => { loadDashboard(); }, []);
  if (loading) return <div className="h-full flex items-center justify-center py-20"><Spinner size="lg" /></div>;
  if (loadError || !status) return <div className="p-6 text-white"><div className="max-w-lg mx-auto mt-20 rounded-2xl border border-rose-500/30 bg-rose-950/30 p-6 text-center"><CircleAlert className="w-7 h-7 text-rose-300 mx-auto" /><h1 className="font-bold mt-3">Dashboard data is temporarily unavailable</h1><p className="text-sm text-slate-400 mt-2">Check that the local backend is running, then retry.</p><button onClick={loadDashboard} className="mt-5 rounded-lg bg-brand-500 px-4 py-2 text-xs font-bold hover:bg-brand-400">Retry dashboard</button></div></div>;
  const sources = [
    ['VDB market', status.vdb_loaded, status.vdb_current_count ?? status.vdb_count, 'Active market snapshot'],
    ['Diamax inventory', status.diamax_loaded, status.diamax_current_count ?? status.diamax_count, 'Available stock snapshot'],
    ['Historical sales', status.sales_loaded, status.sales_unique_count ?? status.sales_count, 'Deduplicated invoice lines'],
  ];
  const ready = sources.filter(source => source[1]).length;
  const actions = [
    ['Review SELL NOW', status.summary?.sell_now_count || 0, 'High-margin opportunities ready for a pricing decision', 'bg-emerald-500/15 text-emerald-300'],
    ['Review WAIT', status.summary?.wait_count || 0, 'Monitor until the market premium improves', 'bg-amber-500/15 text-amber-300'],
    ['Review AVOID', status.summary?.avoid_count || 0, 'Do not allocate further budget without evidence', 'bg-rose-500/15 text-rose-300'],
  ];
  return <div className="p-6 text-white space-y-6 animate-fade-in max-w-[1500px] mx-auto">
    <header className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 border-b border-white/10 pb-5"><div><div className="flex items-center gap-2"><Gem className="w-7 h-7 text-brand-400" /><h1 className="text-2xl font-black">Diamond Intelligence Overview</h1></div><p className="text-sm text-slate-400 mt-2">Start with the data health, then focus on the next pricing decision.</p></div><button onClick={() => navigate('/import')} className="flex items-center gap-2 self-start rounded-xl bg-brand-500 px-5 py-3 text-xs font-black hover:bg-brand-400"><Upload className="w-4 h-4" />Update data files</button></header>
    <section className="rounded-2xl border border-white/10 bg-slate-900/70 p-5"><div className="flex items-center gap-2"><Database className="w-5 h-5 text-cyan-400" /><h2 className="font-bold">Data readiness</h2><span className="ml-auto text-xs text-slate-400">{ready} of 3 sources loaded</span></div><div className="grid md:grid-cols-3 gap-3 mt-4">{sources.map(([name, loaded, count, description]) => <div key={String(name)} className="rounded-xl bg-slate-800/70 border border-white/5 p-4"><div className="flex justify-between"><p className="font-semibold text-sm">{name}</p>{loaded ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <CircleAlert className="w-4 h-4 text-amber-400" />}</div><p className="text-2xl font-black mt-3">{loaded ? number(Number(count)) : 'Missing'}</p><p className="text-xs text-slate-500 mt-1">{description}</p></div>)}</div></section>
    <section className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4"><div className="rounded-2xl bg-gradient-to-br from-brand-600 to-cyan-500 p-5"><p className="text-xs font-bold text-white/75">MATCHED INVENTORY</p><p className="text-3xl font-black mt-2">{number(status.summary?.total_matches || status.matched_count)}</p><p className="text-xs text-white/75 mt-2">Exact VDB-to-Diamax comparables</p></div><div className="rounded-2xl bg-slate-900 border border-white/10 p-5"><p className="text-xs text-slate-400">MATCH RATE</p><p className="text-3xl font-black mt-2">{status.summary?.match_rate || 0}%</p><p className="text-xs text-slate-500 mt-2">Exact comparables ÷ active Diamax stock</p></div><div className="rounded-2xl bg-slate-900 border border-white/10 p-5"><p className="text-xs text-slate-400">AVG PROFIT MARGIN</p><p className="text-3xl font-black mt-2">{(status.summary?.avg_profit_margin || 0).toFixed(1)}%</p><p className="text-xs text-slate-500 mt-2">From matched inventory only</p></div><div className="rounded-2xl bg-slate-900 border border-white/10 p-5"><p className="text-xs text-slate-400">EXPECTED PROFIT</p><p className="text-3xl font-black mt-2">${number(Math.round(status.summary?.total_expected_profit || 0))}</p><p className="text-xs text-slate-500 mt-2">Across recommended selling prices</p></div></section>
    <section className="grid lg:grid-cols-3 gap-5"><div className="lg:col-span-2 rounded-2xl border border-white/10 bg-slate-900/70 p-5"><div className="flex items-center gap-2"><Rocket className="w-5 h-5 text-emerald-400" /><h2 className="font-bold">What needs attention now</h2></div><div className="mt-4 space-y-3">{actions.map(([label, count, description, tone]) => <button key={String(label)} onClick={() => navigate('/ai-pricing')} className="w-full flex items-center gap-4 text-left rounded-xl bg-slate-800/70 hover:bg-slate-800 p-4 transition-colors"><span className={`rounded-lg px-3 py-2 font-black text-lg ${tone}`}>{number(Number(count))}</span><span><span className="block font-bold text-sm">{label}</span><span className="block text-xs text-slate-400 mt-1">{description}</span></span><ArrowRight className="ml-auto w-4 h-4 text-slate-500" /></button>)}</div></div><div className="rounded-2xl border border-white/10 bg-slate-900/70 p-5"><BarChart3 className="w-6 h-6 text-cyan-400" /><h2 className="font-bold mt-3">Recommended path</h2><ol className="mt-4 space-y-3 text-sm text-slate-300"><li><span className="text-brand-400 font-bold">1.</span> Upload all three files.</li><li><span className="text-brand-400 font-bold">2.</span> Review priority actions.</li><li><span className="text-brand-400 font-bold">3.</span> Use the Size Master matrix to compare like-for-like stones.</li></ol><button onClick={() => navigate('/inventory-intelligence')} className="mt-6 text-xs font-bold text-cyan-300 hover:text-cyan-200">Open demand intelligence →</button></div></section>
  </div>;
};
