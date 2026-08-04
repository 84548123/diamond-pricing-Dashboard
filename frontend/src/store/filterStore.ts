import { create } from 'zustand';

interface FilterState {
  shape: string;
  color: string;
  clarity: string;
  recommendation: string;
  minProfit: string;
  maxProfit: string;
  sortBy: string;
  page: number;
  pageSize: number;
  setFilter: (key: keyof FilterState, value: any) => void;
  resetFilters: () => void;
}

const initialState = {
  shape: '',
  color: '',
  clarity: '',
  recommendation: '',
  minProfit: '',
  maxProfit: '',
  sortBy: 'profit_margin_pct',
  page: 1,
  pageSize: 50,
};

export const useFilterStore = create<FilterState>((set) => ({
  ...initialState,
  setFilter: (key, value) => set((state) => ({ ...state, [key]: value, page: key === 'page' || key === 'pageSize' ? value : 1 })),
  resetFilters: () => set(initialState),
}));
