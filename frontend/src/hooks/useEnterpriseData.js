/**
 * Custom hook for fetching enterprise data with loading/error handling
 * Provides consistent data fetching patterns across enterprise pages
 */
import { useState, useEffect } from 'react';

export function useEnterpriseData(fetchFunction, dependencies = []) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const result = await fetchFunction();
      setData(result);
    } catch (err) {
      setError(err.message || 'Failed to load data');
      console.error('Data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, dependencies);

  return {
    loading,
    data,
    error,
    refetch: loadData,
    setData
  };
}
