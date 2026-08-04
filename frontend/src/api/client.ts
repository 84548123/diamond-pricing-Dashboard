import axios from 'axios';
import { StoneSellingMatch, SellingSummary, LeaderboardsData, RuleConfig } from '../types/diamond';

const API_BASE_URL = (import.meta.env.VITE_API_URL || '') + '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

const ADMIN_KEY_STORAGE = 'diamond-admin-key';

export const getAdminKey = () => sessionStorage.getItem(ADMIN_KEY_STORAGE) || '';

export const setAdminKey = (key: string) => {
  const normalized = key.trim();
  if (normalized) sessionStorage.setItem(ADMIN_KEY_STORAGE, normalized);
  else sessionStorage.removeItem(ADMIN_KEY_STORAGE);
};

api.interceptors.request.use((config) => {
  const adminKey = getAdminKey();
  if (adminKey) config.headers.set('X-Admin-Key', adminKey);
  return config;
});

export const getSellingIntelligence = (params: any) => 
  api.get<{ items: StoneSellingMatch[]; total: number; page: number; page_size: number; summary: SellingSummary }>('/selling-intelligence', { params })
    .then(res => res.data);

export const getMatchedStones = getSellingIntelligence;

export const getSummary = () => 
  api.get<SellingSummary>('/summary').then(res => res.data);

export const getDashboardStats = async () => {
  const s = await getSummary();
  return {
    total_vdb_stones: 1500000,
    total_diamax_stones: s.total_inventory || 0,
    total_matches: s.total_matches || 0,
    strong_buy_count: s.sell_now_count || 0,
    buy_count: 0,
    hold_count: 0,
    wait_count: s.wait_count || 0,
    avoid_count: s.avoid_count || 0,
    avg_profit_margin: s.avg_profit_margin || 0,
    total_potential_profit: s.total_expected_profit || 0,
    active_alerts: 0
  };
};

export const getLeaderboards = () => 
  api.get<LeaderboardsData>('/leaderboards').then(res => res.data);

export const getMatrixView = (shape: string = 'ROUND', lab?: string) => 
  api.get<any[]>('/matrix-view', { params: { shape, lab } }).then(res => res.data);

export const getRules = () => 
  api.get<RuleConfig>('/config/rules').then(res => res.data);

export const updateRules = (rules: RuleConfig) => 
  api.post<{ status: string; config: RuleConfig; summary: SellingSummary }>('/config/rules', rules).then(res => res.data);

export const generateSampleData = (vdbCount: number = 1500000, diamaxCount: number = 40000) => 
  api.post<{ status: string; message: string; summary: SellingSummary }>(`/import/generate-sample?vdb_count=${vdbCount}&diamax_count=${diamaxCount}`)
    .then(res => res.data);

export const uploadFiles = (vdbFile: File, diamaxFile: File, salesFile: File) => {
  const formData = new FormData();
  formData.append('vdb_file', vdbFile);
  formData.append('diamax_file', diamaxFile);
  formData.append('sales_file', salesFile);
  // Let the browser supply the multipart boundary. A manually supplied header can
  // leave a large upload pending behind a proxy instead of reaching FastAPI.
  return api.post<{ status: string; message: string; summary: SellingSummary }>('/import/upload', formData, {
    timeout: 5 * 60 * 1000,
  }).then(res => res.data);
};

export const uploadAnyFiles = (files: File[]) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  return api.post<{ status: string; message: string; summary: SellingSummary; detected_sources: Record<string, number> }>('/import/upload-any', formData, {
    timeout: 5 * 60 * 1000,
  }).then(res => res.data);
};

export const downloadExcelReport = () => 
  api.get('/export/excel', { responseType: 'blob' }).then(res => {
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'AI_Diamond_Selling_Intelligence.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

export const downloadPdfReport = () => 
  api.get('/export/pdf', { responseType: 'blob' }).then(res => {
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'AI_Diamond_Selling_Intelligence.pdf');
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

export const downloadExcel = downloadExcelReport;
export const downloadPdf = downloadPdfReport;

export interface MarketRecommendation {
  Shape: string;
  EV_Size_Bucket: string;
  Color: string;
  Clarity: string;
  EV_Stock: number;
  EV_Sold: number;
  Sell_Through: number;
  Demand_Category: string;
  Diamax_Sold: number;
  Diamax_Avg_Sale_Rate: number | null;
  Data_Confidence: string;
  Recommendation: string;
  Reason: string;
  Clearance_Score: number;
  Total_Inventory: number;
  Total_Sold_Quantity: number;
  Available_Stock: number;
  Sales_Percentage: number;
  Stock_Percentage: number;
  Sales_Velocity: number;
  Demand_Score: number;
  Inventory_Risk_Score: number;
}

export interface MarketSummary {
  metrics: { sales_records: number; sales_carats: number; sales_value: number; ev_stock: number; ev_sold: number };
  demand: Record<string, number>;
  confidence: Record<string, number>;
  actions: Record<string, number>;
  shape_summary: Array<{ ShapeName: string; Sold_Stones: number; Sold_Carats: number; Sales_Value: number }>;
  data_limit: string;
}

export const getMarketSummary = () => api.get<MarketSummary>('/market-intelligence/summary').then(res => res.data);
export const getMarketRecommendations = (params: { page: number; page_size: number; search?: string; demand?: string; confidence?: string }) =>
  api.get<{ items: MarketRecommendation[]; total: number }>('/market-intelligence/recommendations', { params }).then(res => res.data);
export const getMarketTopSellers = () => api.get<{ top_sellers: any[]; bottom_sellers: any[] }>('/market-intelligence/top-sellers').then(res => res.data);
export interface RemainingStockOpportunity { shape: string; size_range: string; color: string; clarity: string; sold: number; remaining_stock: number; excess_stock: number; sales_pct: number; demand_score: number; risk_score: number; sell_plan: string; }
export const getRemainingStockOpportunities = () => api.get<{ items: RemainingStockOpportunity[] }>('/market-intelligence/remaining-stock').then(res => res.data);
export interface IndividualStockOpportunity { stone_id: string; carat: number; shape: string; size_range: string; color: string; clarity: string; cut: string; polish: string; symmetry: string; fluorescence: string; lab: string; cohort_stock: number; cohort_sold: number; remaining_stock: number; excess_stock: number; sales_pct: number; current_price: number; current_rate: number | null; historical_rate: number | null; vdb_price: number | null; vdb_rate: number | null; ev_rate: number | null; ai_price: number | null; recommended_rate: number | null; top_1pct_target: number | null; vdb_difference: number | null; market_gap_pct: number | null; sales_source: string; action: string; recommendation: string; }
export interface IndividualStockFacets { shapes: string[]; ranges: string[]; colors: string[]; clarities: string[]; cuts: string[]; polishes: string[]; symmetries: string[]; fluorescences: string[]; labs: string[]; actions: string[]; }
export const getIndividualStockSellThrough = (params?: { shape?: string; size_range?: string; color?: string; clarity?: string; action?: string; search?: string; cut?: string; polish?: string; symmetry?: string; fluorescence?: string; lab?: string }) => api.get<{ items: IndividualStockOpportunity[]; total: number; facets: IndividualStockFacets }>('/market-intelligence/individual-stock-sell-through', { params }).then(res => res.data);
export const getSizeMasterDistribution = () => api.get<{ items: Array<{ size_range: string; sold_stones: number; sold_carats: number; sales_value: number }> }>('/market-intelligence/size-master-distribution').then(res => res.data);
export interface LiveSalesDetail { size_range: string; shape: string; color: string; clarity: string; stock_pcs: number; sold_pcs: number; sales_pct: number | null; current_rate: number | null; historical_rate: number | null; vdb_rate: number | null; sales_30?: number | null; sales_90?: number | null; sales_180?: number | null; sales_history_available?: boolean; inventory_ratio?: number | null; days_inventory?: number | null; ai_rate?: number | null; confidence?: number; action?: string; recommendation_score?: number; reason?: string; }
export const getLiveSalesDetails = () => api.get<{ items: LiveSalesDetail[] }>('/market-intelligence/sales-details-live').then(res => res.data);

export interface ImportStatus {
  vdb_loaded: boolean; vdb_count: number; diamax_loaded: boolean; diamax_count: number;
  sales_loaded: boolean; sales_count: number; matched_count: number; summary: SellingSummary;
}
export const getImportStatus = () => api.get<ImportStatus>('/import/status').then(res => res.data);
export interface ShapeStockVsSales { shape: string; stock_pcs: number; stock_weight: number; stock_rate: number; stock_amount: number; sales_pcs: number; sales_weight: number; sales_rate: number; sales_amount: number; sales_percentage: number; }
export const getShapeStockVsSales = () => api.get<{ items: ShapeStockVsSales[] }>('/market-intelligence/shape-stock-vs-sales').then(res => res.data);
export interface CaratMatrixRow { size_range: string; total_stock: number; total_sold: number; sales_pct: number | null; stock_pct: number | null; vdb_sold_pct: number | null; ev_sold_pct: number | null; demand_score: number | null; inventory_risk_score: number | null; current_price: number | null; historical_selling_price: number | null; suggested_price: number | null; clearance_score: number | null; recommendation: string; confidence: string; available_data: string; missing_data: string; data_coverage: 'Complete' | 'Partial' | 'No data'; price_match_basis: string; }
export interface ColorClarityRow { color: string; clarity: string; sold: number; remaining_stock: number; sales_pct: number | null; demand_score: number; inventory_status: string; }
export interface RangeColorRow { size_range: string; color: string; stock: number; sold: number; sales_pct: number | null; demand_score: number | null; current_price: number | null; suggested_price: number | null; recommendation: string; matched_stock: number; matched_sales: number; }
export interface RangeColorClarityRow { size_range: string; color: string; clarity: string; pieces: number; sold: number; sales_pct: number | null; vdb_pieces: number; vdb_match_pct: number | null; ev_sold_pct: number | null; historical_sales_ratio: number | null; demand_score: number | null; inventory_risk_score: number | null; vdb_price: number | null; ev_price: number | null; diamax_price: number | null; current_price: number | null; historical_price: number | null; ai_price: number | null; discount_markup_pct: number | null; clearance_score: number | null; inventory_status: string; recommendation: string; ai_context?: string; }
export const getCaratMatrixDashboard = (params?: { shape?: string; cut?: string; polish?: string; symmetry?: string; fluorescence?: string; lab?: string; country?: string }) => api.get<{ carat_matrix: CaratMatrixRow[]; color_clarity_matrix: ColorClarityRow[]; range_color_matrix: RangeColorRow[]; range_color_clarity_matrix: RangeColorClarityRow[] }>('/market-intelligence/carat-matrix-dashboard', { params }).then(res => res.data);
export const downloadCaratMatrixExcel = (params: { shape?: string; cut?: string; polish?: string; symmetry?: string; fluorescence?: string; lab?: string; country?: string }) => api.get('/market-intelligence/carat-matrix-export', { params, responseType: 'blob' }).then(res => {
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'Carat_Matrix_Results.xlsx';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
});
