import React, { useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { StoneSellingMatch } from '../../../types/diamond';

interface PriceComparisonGridProps { data: StoneSellingMatch[]; onRowClick: (stone: StoneSellingMatch) => void; }
const money = (value: number | null | undefined) => value == null ? '—' : `$${value.toFixed(2)}`;

export const PriceComparisonGrid: React.FC<PriceComparisonGridProps> = ({ data, onRowClick }) => {
  const columnDefs = useMemo(() => [
    { field: 'diamax_stone_id', headerName: 'Stone ID', width: 135, pinned: 'left', cellStyle: { fontWeight: '600', color: '#67e8f9' } },
    { field: 'shape', headerName: 'Shape', width: 90, pinned: 'left' },
    { field: 'carat', headerName: 'Carat', width: 75, pinned: 'left', valueFormatter: (p: any) => p.value?.toFixed(2) || '—' },
    { field: 'color', headerName: 'Color', width: 70 }, { field: 'clarity', headerName: 'Clarity', width: 80 }, { field: 'lab', headerName: 'Lab', width: 70 },
    { field: 'diamax_price', headerName: 'Current / ct', width: 120, valueFormatter: (p: any) => money(p.value), cellStyle: { color: '#fbbf24', fontWeight: 'bold' } },
    { field: 'min_selling_price', headerName: 'Historical / ct', width: 130, valueFormatter: (p: any) => money(p.value) },
    { field: 'vdb_bottom_price', headerName: 'VDB / ct', width: 110, valueFormatter: (p: any) => money(p.value), cellStyle: { color: '#34d399', fontWeight: 'bold' } },
    { field: 'premium_selling_price', headerName: 'EV / ct', width: 105, valueFormatter: (p: any) => money(p.value), cellStyle: { color: '#fbbf24' } },
    { field: 'recommended_selling_price', headerName: 'Live recommended / ct', width: 165, valueFormatter: (p: any) => money(p.value), cellStyle: (p: any) => ({ color: p.data?.profit_pct < 0 ? '#fda4af' : '#6ee7b7', fontWeight: 'bold' }) },
    { field: 'profit_pct', headerName: 'Price change', width: 115, valueFormatter: (p: any) => p.value == null ? '—' : `${p.value > 0 ? '+' : ''}${p.value.toFixed(1)}%`, cellStyle: (p: any) => ({ color: p.value < 0 ? '#fda4af' : p.value > 0 ? '#6ee7b7' : '#fde68a', fontWeight: 'bold' }) },
    { field: 'competitiveness_score', headerName: 'Sales %', width: 95, valueFormatter: (p: any) => p.value == null ? '—' : `${p.value.toFixed(1)}%` },
    { field: 'action', headerName: 'Live action', width: 170, cellRenderer: (p: any) => <span className={`rounded px-2 py-1 text-xs font-bold ${p.value?.toUpperCase().includes('REDUCE') ? 'bg-rose-500/20 text-rose-300' : p.value?.toUpperCase().includes('INCREASE') ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>{p.value || 'No data'}</span> },
    { field: 'recommendation', headerName: 'Evidence-based reason', width: 340, tooltipField: 'recommendation' },
  ], []);
  const defaultColDef = useMemo(() => ({ sortable: true, resizable: true, filter: true }), []);
  return <div className="ag-theme-alpine-dark h-[650px] w-full overflow-hidden rounded-xl border border-white/10 shadow-2xl"><AgGridReact rowData={data} columnDefs={columnDefs as any} defaultColDef={defaultColDef} rowSelection="single" onRowClicked={(e) => { if (e.data) onRowClick(e.data); }} animateRows rowHeight={48} headerHeight={44} /></div>;
};
