import { useEffect, useState } from 'react';
import { getSizeMasterDistribution } from '../api/client';
import { Spinner } from '../components/ui/Spinner';

type SizeMasterRow = { size_range: string; sold_stones: number; sold_carats: number; sales_value: number };

export const CaratBinAnalysis = () => {
  const [data, setData] = useState<SizeMasterRow[]>([]);

  useEffect(() => { getSizeMasterDistribution().then(result => setData(result.items)); }, []);

  if (!data.length) return <div className="flex min-h-[400px] items-center justify-center"><Spinner size="lg" /></div>;
  const maxSold = Math.max(...data.map(item => item.sold_stones), 1);

  return <div className="h-[calc(100vh-8rem)] min-h-[560px] overflow-hidden animate-fade-in">
    <div className="glass-card flex h-full flex-col p-3">
      <div className="mb-2 flex shrink-0 items-baseline justify-between gap-4">
        <div><h2 className="text-lg font-bold text-white">Size Master Sales Heatmap</h2><p className="mt-0.5 text-[11px] text-slate-400">All 63 exact ranges; darker cells indicate higher sold-piece volume.</p></div>
        <p className="shrink-0 text-xs font-semibold text-cyan-200">{data.length} ranges</p>
      </div>
      <div className="grid flex-1 grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-7 md:[grid-template-rows:repeat(9,minmax(0,1fr))]">
        {data.map(item => {
          const intensity = item.sold_stones / maxSold;
          const background = `rgba(6, ${Math.round(48 + intensity * 120)}, ${Math.round(73 + intensity * 110)}, ${0.3 + intensity * 0.55})`;
          return <div key={item.size_range} title={`${item.size_range} ct: ${item.sold_stones.toLocaleString()} pieces, ${item.sold_carats.toLocaleString(undefined, { maximumFractionDigits: 2 })} ct sold`} style={{ background }} className="flex min-w-0 flex-col justify-center rounded-lg border border-cyan-300/15 px-3 py-1 transition hover:border-cyan-200 hover:ring-1 hover:ring-cyan-300/50">
            <p className="whitespace-nowrap text-xs font-bold text-cyan-100">{item.size_range} ct</p>
            <p className="mt-0.5 text-base font-black text-white">{item.sold_stones.toLocaleString()}<span className="ml-1 text-[10px] font-normal text-slate-200">pcs</span></p>
            <p className="text-[10px] font-semibold text-emerald-100">{item.sold_carats.toLocaleString(undefined, { maximumFractionDigits: 2 })} ct sold</p>
          </div>;
        })}
      </div>
      <div className="mt-2 flex shrink-0 items-center justify-end gap-2 text-[9px] text-slate-400"><span>Lower sales</span><span className="h-2 w-20 rounded" style={{ background: 'linear-gradient(90deg, rgba(6,48,73,.3), rgba(6,168,183,.85))' }} /><span>Higher sales</span></div>
    </div>
  </div>;
};
