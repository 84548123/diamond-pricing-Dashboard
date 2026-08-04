import { Fragment, useEffect, useState } from 'react';
import { Gem } from 'lucide-react';
import type { RangeColorClarityRow } from '../api/client';

const price = (value: number | null | undefined) => value == null ? '-' : value.toFixed(0);
const percent = (value: number | null | undefined) => value == null ? '-' : value.toFixed(0);
const aiAdjustment = (value: number | null | undefined, aiPrice: number | null | undefined, evPrice: number | null | undefined) => {
  if (aiPrice != null && evPrice != null && Math.round(aiPrice) === Math.round(evPrice)) return '-';
  if (value == null || Math.abs(value) < 0.01) return value == null ? '-' : '0';
  return `${value > 0 ? '+' : ''}${value.toFixed(0)}`;
};

const shapes = ['ALL', 'ROUND', 'OVAL', 'EMERALD', 'RADIANT', 'PRINCESS', 'PEAR', 'MARQUISE', 'HEART', 'CUSHION', 'ASSCHER'];

export const VdbPiecesMatrix = ({ rows, shape, onShapeChange }: { rows: RangeColorClarityRow[]; shape: string; onShapeChange: (shape: string) => void }) => {
  const ranges = Array.from(new Set(rows.map(row => row.size_range)));
  const colors = ['D', 'E', 'F', 'G'];
  const clarities = ['VVS1', 'VVS2', 'VS1', 'VS2'];
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(ranges.slice(0, 1)));
  const [selectedRange, setSelectedRange] = useState('ALL');
  const displayedRanges = selectedRange === 'ALL' ? ranges : ranges.filter(range => range === selectedRange);
  const lookup = new Map(rows.map(row => [`${row.size_range}-${row.color}-${row.clarity}`, row]));
  const toggle = (range: string) => setExpanded(current => {
    const next = new Set(current);
    next.has(range) ? next.delete(range) : next.add(range);
    return next;
  });
  useEffect(() => {
    if (selectedRange !== 'ALL') setExpanded(new Set([selectedRange]));
  }, [selectedRange]);

  const clarityPanel = (range: string, clarity: string) => <section key={clarity} className="overflow-hidden rounded-lg border border-white/10 bg-slate-900/35">
    <h3 className="border-b border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-center text-sm font-black text-emerald-200">{clarity}</h3>
    <table className="w-full table-fixed text-[10px]">
      <thead className="bg-slate-800/90 text-slate-300"><tr><th className="w-9 p-1.5 text-left">Color</th><th className="w-12 p-1.5 text-left">Metric</th><th className="p-1.5 text-center text-emerald-200">VDB</th><th className="p-1.5 text-center text-cyan-200">EV</th><th className="p-1.5 text-center text-violet-200">AI Price</th></tr></thead>
      <tbody>{colors.map(color => {
        const item = lookup.get(`${range}-${color}-${clarity}`);
        const rowsForColor = [
          ['Pcs', item?.vdb_pieces?.toLocaleString() ?? '-', item?.pieces?.toLocaleString() ?? '-', '-'],
          ['$ /ct', price(item?.vdb_price), price(item?.diamax_price ?? item?.current_price), price(item?.ai_price)],
          ['Sold %', '-', percent(item?.sales_pct), aiAdjustment(item?.discount_markup_pct, item?.ai_price, item?.diamax_price ?? item?.current_price)],
        ];
        return <Fragment key={color}>{rowsForColor.map(([metric, vdb, diamax, ai], index) => <tr key={`${color}-${metric}`} className={`border-t border-white/5 ${index === 0 ? 'bg-blue-500/[.06]' : ''}`}><td className="p-1.5 text-center font-black text-cyan-200">{index === 1 ? color : ''}</td><td className="p-1.5 font-semibold text-slate-400">{metric}</td><td className="p-1.5 text-center text-emerald-100">{vdb}</td><td className="p-1.5 text-center text-slate-100">{diamax}</td><td className="p-1.5 text-center font-semibold text-violet-100">{ai}</td></tr>)}</Fragment>;
      })}</tbody>
    </table>
  </section>;

  return <div className="glass-card overflow-hidden">
    <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"><h2 className="flex items-center gap-2 font-bold"><Gem className="h-5 w-5 text-emerald-300" />Daily Diamond Matrix</h2><div className="flex flex-wrap gap-2 text-xs"><label className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2 py-1 font-semibold text-slate-700"><span>Shape</span><select value={shape} onChange={event => onShapeChange(event.target.value)} className="bg-transparent font-bold outline-none"><option value="ALL">All Shapes</option>{shapes.slice(1).map(item => <option key={item} value={item}>{item}</option>)}</select></label><label className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2 py-1 font-semibold text-slate-700"><span>Size Range</span><select value={selectedRange} onChange={event => setSelectedRange(event.target.value)} className="bg-transparent font-bold outline-none"><option value="ALL">All Ranges</option>{ranges.map(range => <option key={range} value={range}>{range}</option>)}</select></label></div></div>
    <div>{displayedRanges.map(range => <Fragment key={range}>
      <div className="border-y-2 border-blue-500/70 bg-blue-500/15"><button type="button" onClick={() => toggle(range)} className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-blue-500/20"><span className="flex h-5 w-5 items-center justify-center rounded-md bg-blue-500/70 text-sm font-black">{expanded.has(range) ? '-' : '+'}</span><span className="text-xs font-black">Size: {range}</span></button>{expanded.has(range) && <div className="flex flex-wrap gap-1 border-t border-blue-400/30 px-3 py-1.5">{shapes.map(item => <button key={item} type="button" onClick={() => onShapeChange(item)} className={`rounded px-2 py-0.5 text-[9px] font-bold ${shape === item ? 'bg-cyan-300 text-slate-950' : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'}`}>{item === 'ALL' ? 'All Shapes' : item}</button>)}</div>}</div>
      {expanded.has(range) && <div className="grid gap-3 p-3 md:grid-cols-2 xl:grid-cols-4">{clarities.map(clarity => clarityPanel(range, clarity))}</div>}
    </Fragment>)}</div>
  </div>;
};
