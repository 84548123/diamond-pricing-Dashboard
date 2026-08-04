import React, { useEffect, useMemo, useState } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { ExportButtons } from '../components/shared/ExportButtons';
import { getLiveSalesDetails, LiveSalesDetail } from '../api/client';
import { Spinner } from '../components/ui/Spinner';

type Filters = { shape: string; size: string; color: string; clarity: string; action: string; confidence: string; opportunity: string; stock: string; sales: string; gap: string; search: string };
const emptyFilters: Filters = { shape: '', size: '', color: '', clarity: '', action: '', confidence: '', opportunity: '', stock: '', sales: '', gap: '', search: '' };
const compact = (value: number | null | undefined) => value == null ? '-' : new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
const price = (value: number | null | undefined) => value == null ? '-' : value.toFixed(1);

const opportunityFor = (row: LiveSalesDetail) => {
  const current = row.current_rate ?? 0; const vdb = row.vdb_rate ?? 0; const sales = row.sales_pct ?? 0; const ratio = row.inventory_ratio ?? 0;
  if ((row.confidence ?? 0) < 40) return 'Manual Review';
  if (sales > 100 || (ratio > 0 && ratio < 0.5)) return 'High Demand';
  if (vdb && current < vdb * 0.97) return 'Underpriced';
  if (ratio > 2) return 'Overstock';
  if (vdb && current > vdb * 1.03) return 'Overpriced';
  if (!row.sales_history_available) return 'Limited Market Data';
  return 'Normal';
};

const opportunityRank = (row: LiveSalesDetail) => {
  const opportunity = opportunityFor(row);
  if (opportunity === 'High Demand') return 0;
  if (opportunity === 'Underpriced') return 1;
  if (String(row.action).startsWith('Increase')) return 2;
  if (opportunity === 'Overstock') return 3;
  if (opportunity === 'Manual Review') return 4;
  return 5;
};

const confidenceClass = (value?: number) => value == null ? 'text-slate-400' : value > 90 ? 'text-emerald-200' : value >= 75 ? 'text-emerald-400' : value >= 50 ? 'text-amber-300' : 'text-rose-400';
const salesClass = (value?: number | null) => value == null ? 'text-slate-400' : value > 100 ? 'text-emerald-300' : value >= 50 ? 'text-amber-300' : 'text-rose-400';

export const SalesDetails = () => {
  const [rows, setRows] = useState<LiveSalesDetail[]>([]);
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  useEffect(() => { getLiveSalesDetails().then(result => setRows(result.items)); }, []);

  const values = (field: keyof Pick<LiveSalesDetail, 'shape' | 'size_range' | 'color' | 'clarity' | 'action'>) => [...new Set(rows.map(row => String(row[field] || '')).filter(Boolean))].sort();
  const filteredRows = useMemo(() => rows.filter(row => {
    const confidence = row.confidence ?? 0; const stock = row.stock_pcs ?? 0; const sales = row.sales_pct ?? 0;
    const gap = row.vdb_rate ? ((row.current_rate ?? 0) - row.vdb_rate) / row.vdb_rate * 100 : null;
    const matrix = `${row.shape} ${row.size_range} ${row.color} ${row.clarity}`.toLowerCase();
    return (!filters.shape || row.shape === filters.shape) && (!filters.size || row.size_range === filters.size) && (!filters.color || row.color === filters.color) && (!filters.clarity || row.clarity === filters.clarity) && (!filters.action || row.action === filters.action)
      && (!filters.confidence || (filters.confidence === 'Very High' ? confidence >= 95 : filters.confidence === 'High' ? confidence >= 80 && confidence < 95 : filters.confidence === 'Medium' ? confidence >= 60 && confidence < 80 : filters.confidence === 'Low' ? confidence >= 40 && confidence < 60 : confidence < 40))
      && (!filters.opportunity || opportunityFor(row) === filters.opportunity) && (!filters.stock || (filters.stock === 'High (50+)' ? stock >= 50 : stock < 50)) && (!filters.sales || (filters.sales === 'High (100%+)' ? sales > 100 : filters.sales === 'Medium (50-100%)' ? sales >= 50 && sales <= 100 : sales < 50))
      && (!filters.gap || (filters.gap === 'Above VDB (3%+)' ? (gap ?? 0) >= 3 : (gap ?? 0) <= -3)) && (!filters.search || matrix.includes(filters.search.toLowerCase()));
  }).sort((a, b) => opportunityRank(a) - opportunityRank(b) || (b.recommendation_score ?? 0) - (a.recommendation_score ?? 0)), [rows, filters]);

  const columnDefs = useMemo(() => [
    { headerName: 'Matrix (Shape | Size Range | Color | Clarity)', width: 230, pinned: 'left', wrapHeaderText: true, valueGetter: (p: any) => `${p.data.shape} | ${p.data.size_range} | ${p.data.color} | ${p.data.clarity}`, cellStyle: { fontWeight: '700', color: '#e2e8f0', textAlign: 'left' } },
    { headerName: 'Current Stock', width: 84, wrapHeaderText: true, valueGetter: (p: any) => compact(p.data.stock_pcs), cellStyle: { textAlign: 'center' } },
    { headerName: 'Historical Sales', width: 94, wrapHeaderText: true, valueGetter: (p: any) => p.data.sales_history_available ? compact(p.data.sold_pcs) : 'N/A (No Sales History)', cellStyle: { textAlign: 'center', fontSize: '11px' } },
    { headerName: 'Sales Percentage', width: 92, wrapHeaderText: true, cellRenderer: (p: any) => <span className={salesClass(p.data.sales_pct)}>{p.data.sales_pct == null ? '-' : `${p.data.sales_pct}%`}</span>, cellStyle: { textAlign: 'center' } },
    { headerName: 'Inventory Ratio', width: 98, wrapHeaderText: true, cellRenderer: (p: any) => p.data.inventory_ratio == null ? <span className="text-slate-400">N/A (No Sales History)</span> : <span className={p.data.inventory_ratio <= 1.2 ? 'text-emerald-300' : p.data.inventory_ratio <= 2 ? 'text-amber-300' : 'text-rose-400'}>{p.data.inventory_ratio} {p.data.inventory_ratio <= .5 ? 'Short Supply' : p.data.inventory_ratio <= 1.2 ? 'Healthy' : p.data.inventory_ratio <= 2 ? 'Overstock' : 'Excess'}</span>, cellStyle: { textAlign: 'center', fontSize: '11px' } },
    { headerName: 'Current Price ($/ct)', width: 112, wrapHeaderText: true, cellRenderer: (p: any) => { const current = p.data.current_rate; const ai = p.data.ai_rate; const delta = current && ai ? (current - ai) / ai : 0; return <span className={delta < -.01 ? 'text-emerald-300' : delta > .01 ? 'text-rose-400' : 'text-slate-300'}>{price(current)}</span>; }, cellStyle: { textAlign: 'center' } },
    { headerName: 'Historical Price ($/ct)', width: 120, wrapHeaderText: true, valueGetter: (p: any) => price(p.data.historical_rate), cellStyle: { textAlign: 'center' } },
    { headerName: 'VDB Market Price ($/ct)', width: 125, wrapHeaderText: true, valueGetter: (p: any) => price(p.data.vdb_rate), cellStyle: { textAlign: 'center', color: '#34d399' } },
    { headerName: 'AI Recommended Price ($/ct)', width: 135, wrapHeaderText: true, valueGetter: (p: any) => price(p.data.ai_rate), cellStyle: { textAlign: 'center', color: '#67e8f9', fontWeight: '700' } },
    { headerName: 'Recommendation Confidence', width: 115, wrapHeaderText: true, cellRenderer: (p: any) => <span className={confidenceClass(p.data.confidence)}>{p.data.confidence ?? '-'}%<span className="ml-1 text-[10px] opacity-80">{p.data.confidence >= 95 ? 'Very High' : p.data.confidence >= 80 ? 'High' : p.data.confidence >= 60 ? 'Medium' : p.data.confidence >= 40 ? 'Low' : 'Very Low'}</span></span>, cellStyle: { textAlign: 'center' } },
    { headerName: 'Recommended Action', width: 112, wrapHeaderText: true, cellRenderer: (p: any) => { const action = String(p.data.action || 'Manual Review'); const style = action.startsWith('Increase') ? 'bg-emerald-500/20 text-emerald-300' : action.startsWith('Reduce') ? 'bg-rose-500/20 text-rose-300' : action === 'Promote' ? 'bg-amber-500/20 text-amber-300' : action === 'Hold' ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-600/50 text-slate-200'; return <span title={p.data.reason} className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${style}`}>{action}</span>; }, cellStyle: { textAlign: 'center' } },
  ], []);

  const select = (key: keyof Filters, label: string, options: string[]) => <label><span className="sr-only">{label}</span><select value={filters[key]} onChange={event => setFilters(current => ({ ...current, [key]: event.target.value }))} className="h-8 min-w-[110px] rounded-md border border-white/10 bg-slate-800 px-2 text-xs text-slate-100 outline-none transition focus:border-cyan-400"><option value="">{label} ▼</option>{options.map(option => <option key={option} value={option}>{option}</option>)}</select></label>;
  if (!rows.length) return <div className="flex min-h-[400px] items-center justify-center"><Spinner size="lg" /></div>;

  return <div className="sales-matrix flex h-full min-h-screen flex-col space-y-3 animate-fade-in">
    <div className="glass-card flex items-center justify-between p-3"><div><h2 className="text-base font-bold text-white">Sales Details - Commercial Decision Matrix</h2><p className="mt-0.5 text-xs text-slate-400">Rows are ranked for sales action: demand, underpricing, increase opportunities, overstock, then manual review.</p></div><ExportButtons /></div>
    <div className="glass-card sticky top-0 z-20 p-3"><div className="flex flex-wrap items-center gap-2">{select('shape', 'Shape', values('shape'))}{select('size', 'Size', values('size_range'))}{select('color', 'Color', values('color'))}{select('clarity', 'Clarity', values('clarity'))}{select('action', 'Recommendation', values('action'))}{select('confidence', 'Confidence', ['Very High', 'High', 'Medium', 'Low', 'Very Low'])}{select('opportunity', 'Opportunity', ['High Demand', 'Underpriced', 'Overstock', 'Overpriced', 'Limited Market Data', 'Manual Review', 'Normal'])}{select('stock', 'Stock', ['High (50+)', 'Low (<50)'])}{select('sales', 'Sales %', ['High (100%+)', 'Medium (50-100%)', 'Low (<50%)'])}{select('gap', 'Price Gap', ['Above VDB (3%+)', 'Below VDB (3%+)'])}<input value={filters.search} onChange={event => setFilters(current => ({ ...current, search: event.target.value }))} placeholder="Search Matrix" className="h-8 min-w-[145px] rounded-md border border-white/10 bg-slate-800 px-2 text-xs text-slate-100 placeholder:text-slate-400 outline-none transition focus:border-cyan-400" /><button type="button" onClick={() => setFilters(emptyFilters)} className="h-8 rounded-md border border-white/10 px-2 text-xs text-slate-300 hover:bg-white/5">Clear</button><span className="ml-auto text-xs text-slate-400">{filteredRows.length.toLocaleString()} of {rows.length.toLocaleString()}</span></div></div>
    <div className="glass-card min-h-[680px] flex-1 overflow-hidden p-1"><div className="ag-theme-alpine-dark h-full w-full"><AgGridReact rowData={filteredRows} columnDefs={columnDefs as any} defaultColDef={{ sortable: true, resizable: false, wrapHeaderText: true, autoHeaderHeight: true }} animateRows rowHeight={34} headerHeight={42} suppressHorizontalScroll suppressCellFocus /></div></div>
    <style>{`.sales-matrix .ag-cell { font-size: 12px; padding-left: 6px; padding-right: 6px; line-height: 32px; } .sales-matrix .ag-header-cell-text { font-size: 13px; line-height: 15px; } .sales-matrix .ag-header-cell-label { justify-content: center; } .sales-matrix .ag-pinned-left-header .ag-header-cell-label { justify-content: flex-start; }`}</style>
  </div>;
};
