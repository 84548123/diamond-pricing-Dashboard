import { useEffect, useState } from 'react';
import { AlertTriangle, Gem, TrendingDown, TrendingUp } from 'lucide-react';
import {
  getIndividualStockSellThrough,
  getMarketSummary,
  IndividualStockFacets,
  IndividualStockOpportunity,
  MarketSummary,
} from '../api/client';
import { Spinner } from '../components/ui/Spinner';

const emptyFacets: IndividualStockFacets = { shapes: [], ranges: [], colors: [], clarities: [], cuts: [], polishes: [], symmetries: [], fluorescences: [], labs: [], actions: [] };
const rate = (value: number | null | undefined) => value == null ? '—' : `$${value.toFixed(2)}`;

const Action = ({ stone }: { stone: IndividualStockOpportunity }) => {
  const change = stone.recommended_rate != null && stone.current_rate
    ? (stone.recommended_rate / stone.current_rate - 1) * 100 : 0;
  const tone = change < -0.5 ? 'text-rose-300' : change > 0.5 ? 'text-emerald-300' : 'text-amber-300';
  return <div><p className={`font-bold ${tone}`}>{stone.action}</p><p className="mt-1 max-w-sm text-slate-400">{stone.recommendation}</p></div>;
};

export const InventoryIntelligence = () => {
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [stones, setStones] = useState<IndividualStockOpportunity[]>([]);
  const [total, setTotal] = useState(0);
  const [facets, setFacets] = useState<IndividualStockFacets>(emptyFacets);
  const [filters, setFilters] = useState({ search: '', shape: '', range: '', color: '', clarity: '', cut: '', polish: '', symmetry: '', fluorescence: '', lab: '', action: '' });

  useEffect(() => { getMarketSummary().then(setSummary); }, []);

  useEffect(() => {
    let active = true;
    getIndividualStockSellThrough({
      shape: filters.shape || undefined,
      size_range: filters.range || undefined,
      color: filters.color || undefined,
      clarity: filters.clarity || undefined,
      cut: filters.cut || undefined,
      polish: filters.polish || undefined,
      symmetry: filters.symmetry || undefined,
      fluorescence: filters.fluorescence || undefined,
      lab: filters.lab || undefined,
      action: filters.action || undefined,
      search: filters.search || undefined,
    }).then(report => {
      if (!active) return;
      setStones(report.items);
      setTotal(report.total);
      setFacets(report.facets);
    });
    return () => { active = false; };
  }, [filters.shape, filters.range, filters.color, filters.clarity, filters.cut, filters.polish, filters.symmetry, filters.fluorescence, filters.lab, filters.action, filters.search]);

  const filtered = stones;
  const set = (key: keyof typeof filters, value: string) => setFilters(current => ({ ...current, [key]: value }));
  const summaryCards = summary ? [
    ['Current inventory', summary.metrics.ev_stock.toLocaleString(), Gem, 'text-cyan-300'],
    ['Historical sales', summary.metrics.sales_records.toLocaleString(), TrendingUp, 'text-emerald-300'],
    ['Matching excess-stock stones', total.toLocaleString(), AlertTriangle, 'text-rose-300'],
    ['Visible rows', filtered.length.toLocaleString(), TrendingDown, 'text-amber-300'],
  ] : [];

  if (!summary) return <div className="flex min-h-[400px] items-center justify-center"><Spinner size="lg" /></div>;

  const select = (label: string, value: string, options: string[], onChange: (value: string) => void) => (
    <select value={value} onChange={event => onChange(event.target.value)} className="rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-xs">
      <option value="">{label}</option>
      {options.map(option => <option key={option} value={option}>{option}</option>)}
    </select>
  );

  return <div className="min-h-screen bg-slate-950 p-6 text-white animate-fade-in">
    <div className="mx-auto max-w-[1800px]">
      <header className="mb-6 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-500/15 p-2.5"><Gem className="h-6 w-6 text-cyan-300" /></div>
          <div><h1 className="text-2xl font-black">Inventory Intelligence — Action Board</h1><p className="mt-1 text-sm text-slate-400">Current, historical, VDB and EV rates are compared on the same per-carat basis. Recommendation colour follows the calculated price change.</p></div>
        </div>
      </header>

      <section className="mb-6 grid grid-cols-2 gap-4 xl:grid-cols-4">
        {summaryCards.map(([title, value, Icon, tone]: any) => <div key={title} className="rounded-2xl border border-white/10 bg-slate-900/80 p-4"><Icon className={`h-5 w-5 ${tone}`} /><p className="mt-3 text-xs text-slate-400">{title}</p><p className="mt-1 text-2xl font-black">{value}</p></div>)}
      </section>

      <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80">
        <div className="border-b border-white/10 p-5">
          <h2 className="font-bold">Stone-level Sell-Through & Pricing Recommendation</h2>
          <p className="mt-1 text-xs text-slate-400">Recommended sell / ct uses the individual stone’s exact VDB comparable (40%), compatible historical sales (45%) and EV evidence (15%), then applies a clearance adjustment. Shared sell-through is shown only where the sales source is genuinely aggregated.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <input value={filters.search} onChange={event => set('search', event.target.value)} placeholder="Search exact stone ID or cohort" className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-xs outline-none focus:border-cyan-400 sm:w-52" />
            {select('All shapes', filters.shape, facets.shapes, value => set('shape', value))}
            {select('All carat ranges', filters.range, facets.ranges, value => set('range', value))}
            {select('All colors', filters.color, facets.colors, value => set('color', value))}
            {select('All clarities', filters.clarity, facets.clarities, value => set('clarity', value))}
            {select('All cuts', filters.cut, facets.cuts, value => set('cut', value))}
            {select('All polish', filters.polish, facets.polishes, value => set('polish', value))}
            {select('All symmetry', filters.symmetry, facets.symmetries, value => set('symmetry', value))}
            {select('All fluorescence', filters.fluorescence, facets.fluorescences, value => set('fluorescence', value))}
            {select('All labs', filters.lab, facets.labs, value => set('lab', value))}
            {select('All actions', filters.action, facets.actions, value => set('action', value))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1440px] text-xs">
            <thead className="sticky top-0 z-20 bg-slate-800/95 text-left text-slate-300"><tr><th className="p-3">Stone</th><th className="p-3">Matched profile</th><th className="p-3 text-right">Stock / Sold</th><th className="p-3 text-right">Sales %</th><th className="p-3 text-right">Current / ct</th><th className="p-3 text-right">Historical / ct</th><th className="p-3 text-right">VDB / ct</th><th className="p-3 text-right">EV / ct</th><th className="p-3 text-right">Recommended / ct</th><th className="p-3">Recommendation</th></tr></thead>
            <tbody>{filtered.map(stone => {
              const delta = stone.recommended_rate != null && stone.current_rate ? (stone.recommended_rate / stone.current_rate - 1) * 100 : 0;
              const rateTone = delta < -0.5 ? 'text-rose-300' : delta > 0.5 ? 'text-emerald-300' : 'text-amber-300';
              return <tr key={stone.stone_id} className="border-t border-white/5 hover:bg-white/[.03]"><td className="p-3 font-mono text-cyan-200">{stone.stone_id}<p className="mt-1 font-sans text-slate-500">{stone.carat} ct</p></td><td className="p-3"><p className="font-semibold">{stone.shape} · {stone.size_range} · {stone.color} · {stone.clarity}</p><p className="mt-1 text-slate-500">{stone.cut || '—'} Cut · {stone.polish || '—'} Pol · {stone.symmetry || '—'} Sym</p><p className="mt-1 text-slate-500">{stone.fluorescence || '—'} Fluor · {stone.lab || '—'} Lab</p></td><td className="p-3 text-right">{stone.cohort_stock} / {stone.cohort_sold}<p className="mt-1 text-rose-300">+{stone.excess_stock} excess</p></td><td className="p-3 text-right">{stone.sales_pct}%</td><td className="p-3 text-right">{rate(stone.current_rate)}</td><td className="p-3 text-right">{rate(stone.historical_rate)}</td><td className="p-3 text-right text-emerald-300">{rate(stone.vdb_rate)}<p className="mt-1 text-[10px] text-slate-500">{stone.market_gap_pct != null ? `${stone.market_gap_pct > 0 ? '+' : ''}${stone.market_gap_pct}% vs current` : 'No exact match'}</p></td><td className="p-3 text-right text-amber-300">{rate(stone.ev_rate)}</td><td className={`p-3 text-right font-black ${rateTone}`}>{rate(stone.recommended_rate)}<p className="mt-1 text-[10px]">{delta ? `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%` : '—'}</p></td><td className="p-3"><Action stone={stone} /></td></tr>;
            })}</tbody>
          </table>
        </div>
      </section>
    </div>
  </div>;
};
