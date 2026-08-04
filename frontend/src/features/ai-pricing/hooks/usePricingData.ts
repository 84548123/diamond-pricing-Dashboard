import { useState, useEffect, useCallback } from 'react';
import * as api from '../../../api/client';
import { useFilterStore } from '../../../store/filterStore';
import { StoneMatch } from '../../../types/diamond';

export const usePricingData = () => {
  const filters = useFilterStore();
  const [data, setData] = useState<StoneMatch[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStones = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        shape: filters.shape,
        color: filters.color,
        clarity: filters.clarity,
        recommendation: filters.recommendation,
        min_profit: filters.minProfit,
        max_profit: filters.maxProfit,
        sort_by: filters.sortBy,
        page: filters.page,
        page_size: filters.pageSize
      };
      
      const response = await api.getMatchedStones(params);
      setData(response.items);
      setTotal(response.total);
      setSummary(response.summary);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pricing data');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchStones();
  }, [fetchStones]);

  return { data, total, summary, loading, error, refetch: fetchStones };
};
