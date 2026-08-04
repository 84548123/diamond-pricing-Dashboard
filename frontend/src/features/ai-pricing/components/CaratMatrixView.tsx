import React, { Fragment, useEffect, useState } from 'react';
import { getCaratMatrixDashboard, RangeColorClarityRow } from '../../../api/client';
import { Spinner } from '../../../components/ui/Spinner';
import { ChevronDown, ChevronRight, Grid } from 'lucide-react';

export const CaratMatrixView: React.FC = () => {
  const [rows, setRows] = useState<RangeColorClarityRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [collapsedRanges, setCollapsedRanges] = useState<Record<string, boolean>>({});
  useEffect(() => {
    getCaratMatrixDashboard().then(result => setRows(result.range_color_clarity_matrix)).finally(() => setLoading(false));
  }, []);
  const ranges = Array.from(new Set(rows.map(row => row.size_range)));
  const colors = ['D', 'E', 'F', 'G'];
  const clarities = ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1'];
  const lookup = new Map(rows.map(row => [`${row.size_range}-${row.color}-${row.clarity}`, row]));
  const price = (value: number | null | undefined) => value == null ? '—' : `$${value.toFixed(0)}`;
  const toggleRange = (range: string) => setCollapsedRanges(current => ({ ...current, [range]: !current[range] }));

  return <div className="bg-slate-950 p-6 rounded-2xl border border-white/10 text-white animate-fade-in shadow-2xl">
    <div className="mb-6 border-b border-white/10 pb-4"><h2 className="text-2xl font-black flex items-center gap-2.5"><Grid className="w-6 h-6 text-brand-400" />AI Selling Intelligence Matrix</h2><p className="text-xs text-slate-400 mt-1">Standardized with the Daily Carat Matrix: real VDB comparables, EV Stock-vs-Sold prices, and sales-qualified AI targets. All prices are $/ct.</p></div>
    {loading ? <div className="py-20 flex flex-col items-center justify-center"><Spinner size="lg" /><span className="text-xs text-slate-400 mt-3 font-semibold">Loading standardized comparison matrix...</span></div> : <div className="space-y-4 overflow-x-auto">{ranges.map(range => { const collapsed = collapsedRanges[range]; const rangeRows = rows.filter(row => row.size_range === range); return <div key={range} className="border border-slate-700/80 rounded-xl overflow-hidden shadow-lg bg-slate-900/60"><button type="button" onClick={() => toggleRange(range)} className="w-full bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 hover:from-slate-800 p-3 flex items-center justify-between border-b border-slate-700/60"><div className="flex items-center space-x-3"><span className="p-1 bg-brand-500/20 text-brand-400 rounded-md">{collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</span><span className="font-extrabold text-sm">Carat range: {range}</span><span className="text-xs text-slate-400">{rangeRows.length} compatible Color × Clarity combinations</span></div></button>{!collapsed && <div className="overflow-x-auto"><table className="w-full min-w-[1480px] text-[10px] text-center border-collapse"><thead><tr className="bg-slate-900 border-b border-slate-700/80"><th className="p-2 border-r border-slate-700/60 text-slate-300">Color</th>{clarities.map(clarity => <th key={clarity} className="p-2 border-r border-slate-700/60 text-emerald-200">{clarity}</th>)}</tr></thead><tbody>{colors.map(color => <tr key={color} className="border-b border-slate-800/80 hover:bg-slate-800/40"><td className="p-2 border-r border-slate-700/60 font-black text-amber-400 bg-slate-900/40">{color}</td>{clarities.map(clarity => { const cell = lookup.get(`${range}-${color}-${clarity}`); const reduce = cell?.ai_price != null && cell.current_price != null && cell.ai_price < cell.current_price; return <td key={clarity} className="p-1 border-r border-slate-800/50"><div className="min-h-[56px] rounded-md border border-white/10 bg-slate-800/70"><div className="grid grid-cols-3 border-b border-white/10"><span className="py-1 text-slate-400">P {cell?.pieces ?? '—'}</span><span className="py-1 border-x border-white/10 text-cyan-200">S {cell?.sales_pct != null ? `${cell.sales_pct}%` : '—'}</span><span className="py-1 text-slate-400">{cell?.inventory_status ?? '—'}</span></div><div className="grid grid-cols-3 py-1"><span className="text-emerald-300">V {price(cell?.vdb_price)}</span><span className="text-amber-300">E {price(cell?.ev_price)}</span><span className={reduce ? 'text-rose-300 font-black' : 'text-cyan-300 font-black'}>AI {price(cell?.ai_price)}</span></div></div></td>; })}</tr>)}</tbody></table></div>}</div>; })}</div>}
  </div>;
};
