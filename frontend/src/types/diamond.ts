export type SellingAction = 'SELL NOW' | 'WAIT' | 'AVOID' | 'NO MATCH FOUND';
export type Recommendation = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'WAIT' | 'AVOID';

export interface SellingSummary {
  total_inventory: number;
  total_matches: number;
  match_rate: number;
  sell_now_count: number;
  wait_count: number;
  avoid_count: number;
  avg_profit_margin: number;
  total_expected_profit: number;
  max_profit: number;
  avg_competitiveness: number;
}

export interface StoneSellingMatch {
  diamax_stone_id: string;
  vdb_stone_id?: string;
  shape: string;
  carat: number;
  color: string;
  clarity: string;
  cut: string;
  polish: string;
  symmetry: string;
  fluorescence: string;
  lab: string;
  country: string;
  vdb_bottom_price: number | null;
  diamax_price: number;
  market_diff_abs: number | null;
  market_diff_pct: number | null;
  min_selling_price: number | null;
  recommended_selling_price: number | null;
  premium_selling_price: number | null;
  expected_profit: number;
  profit_pct: number;
  negotiation_range: string;
  competitiveness_score: number;
  vdb_top_1pct_price?: number | null;
  top_1pct_listing_price?: number | null;
  top_1pct_status?: string;
  recommendation: string;
  action: SellingAction;
}

export type StoneMatch = StoneSellingMatch;

export interface DashboardStats {
  total_vdb_stones: number;
  total_diamax_stones: number;
  total_matches: number;
  strong_buy_count: number;
  buy_count: number;
  hold_count: number;
  wait_count: number;
  avoid_count: number;
  avg_profit_margin: number;
  total_potential_profit: number;
  active_alerts: number;
}

export interface RuleConfig {
  premium_threshold: number;
  sell_now_threshold: number;
  good_opp_threshold: number;
  wait_threshold: number;
}

export interface LeaderboardsData {
  top_profitable: StoneSellingMatch[];
  top_sell_now: StoneSellingMatch[];
  top_premium_opps: StoneSellingMatch[];
  top_margin: StoneSellingMatch[];
  top_wait: StoneSellingMatch[];
  lowest_margin: StoneSellingMatch[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  summary?: any;
}
