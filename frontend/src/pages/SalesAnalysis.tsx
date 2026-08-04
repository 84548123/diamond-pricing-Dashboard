import { useEffect, useMemo, useState } from 'react';
import { BarChart, Bar, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ShoppingCart, TrendingUp, AlertTriangle, BarChart3 } from 'lucide-react';
import { getShapeStockVsSales, ShapeStockVsSales } from '../api/client';
import { Card } from '../components/ui/Card';
import { Spinner } from '../components/ui/Spinner';

const format = (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 1 });

export const SalesAnalysis = () => {
  const [data, setData] = useState<ShapeStockVsSales[]>([]);
  useEffect(() => { getShapeStockVsSales().then(result => setData(result.items)); }, []);
  const totals = useMemo(() => data.reduce((sum, row) => ({ stock: sum.stock + row.stock_pcs, sold: sum.sold + row.sales_pcs, salesAmount: sum.salesAmount + row.sales_amount }), { stock: 0, sold: 0, salesAmount: 0 }), [data]);
  if (!data.length) return <div className="min-h-[400px] flex items-center justify-center"><Spinner size="lg" /></div>;
  const salesPct = totals.stock ? totals.sold / totals.stock * 100 : 0;
  const best = [...data].sort((a, b) => b.sales_percentage - a.sales_percentage)[0];
  const risk = [...data].sort((a, b) => a.sales_percentage - b.sales_percentage)[0];
  return <div className="space-y-6 animate-fade-in">
    <div className="glass-card p-6"><div className="flex items-center gap-3"><div className="p-2 rounded-xl bg-emerald-500/15"><BarChart3 className="w-6 h-6 text-emerald-300" /></div><div><h1 className="text-xl font-black text-white">Sales Analysis</h1><p className="text-xs text-slate-400 mt-1">Sales % is calculated using the current formula: Sold Pieces ÷ Remaining Stock Pieces × 100.</p></div></div></div>
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4"><Card title="Remaining Stock" value={format(totals.stock)} icon={ShoppingCart} gradient="from-cyan-500 to-blue-500" /><Card title="Sold Pieces" value={format(totals.sold)} icon={TrendingUp} gradient="from-emerald-500 to-teal-400" /><Card title="Sales %" value={`${salesPct.toFixed(1)}%`} icon={BarChart3} gradient="from-amber-500 to-orange-400" /><Card title="Sales Value" value={`$${format(totals.salesAmount)}`} icon={AlertTriangle} gradient="from-violet-500 to-fuchsia-400" /></div>
    <div className="grid lg:grid-cols-3 gap-5"><div className="lg:col-span-2 glass-card p-6"><h2 className="font-bold text-white">Sold vs Remaining Stock</h2><div className="h-[380px] mt-4"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.slice(0, 12)} margin={{ top: 10, right: 20, left: 0, bottom: 55 }}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} /><XAxis dataKey="shape" stroke="#94a3b8" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 11 }} /><YAxis stroke="#94a3b8" /><Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,.12)', borderRadius: '8px' }} /><Legend /><Bar dataKey="stock_pcs" name="Remaining Stock" fill="#38bdf8" radius={[4, 4, 0, 0]} /><Bar dataKey="sales_pcs" name="Sold" fill="#34d399" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></div><div className="glass-card p-6"><h2 className="font-bold text-white">Quick read</h2><div className="mt-5 space-y-4"><div className="rounded-xl bg-emerald-500/10 p-4"><p className="text-xs text-emerald-300">BEST SALES %</p><p className="font-black text-lg mt-1">{best.shape}</p><p className="text-sm text-emerald-200">{best.sales_percentage}% sold vs stock</p></div><div className="rounded-xl bg-rose-500/10 p-4"><p className="text-xs text-rose-300">LOWEST SALES %</p><p className="font-black text-lg mt-1">{risk.shape}</p><p className="text-sm text-rose-200">{risk.sales_percentage}% sold vs stock</p></div><p className="text-xs text-slate-400">Use low sales % with high remaining stock as the first signal for promotion, price review, or liquidation.</p></div></div></div>
  </div>;
};
