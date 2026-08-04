import { useState, useEffect } from 'react';

export const usePriceHistory = (matchId: string, initialPeriod: string = '24h') => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async (period: string) => {
    if (!matchId) return;
    setLoading(true);
    try {
      setData({ history: [] });
    } catch (err: any) {
      setError(err.message || 'Failed to fetch history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(initialPeriod);
  }, [matchId, initialPeriod]);

  return { data, loading, error, refetch: fetchHistory };
};
