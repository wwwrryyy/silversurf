import { useState, useEffect, useCallback } from 'react';
import { HistoricalRateRecord, HistoryQueryParams, SessionType } from '../types';
import { formatISTDateISO, getISTDateRange } from '../utils/formatters';

export function useRateHistory(initialParams: HistoryQueryParams = {}) {
  const [records, setRecords] = useState<HistoricalRateRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [sessionFilter, setSessionFilter] = useState<SessionType | 'ALL'>('ALL');
  const [rangeFilter, setRangeFilter] = useState<'7D' | '30D' | '90D' | 'ALL'>('30D');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(initialParams.limit || 50);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      params.set('format', 'json');
      params.set('limit', pageSize.toString());
      params.set('offset', ((page - 1) * pageSize).toString());

      if (sessionFilter !== 'ALL') {
        params.set('session', sessionFilter);
      }

      // Compute date boundaries for range
      const range = getISTDateRange(rangeFilter);
      if (range) {
        params.set('from', range.fromDate);
        params.set('to', range.toDate);
      }

      const res = await fetch(`/v1/silver?${params.toString()}`, {
        headers: { Accept: 'application/json' },
      });

      if (!res.ok) {
        throw new Error(`Failed to load rate history: HTTP ${res.status}`);
      }

      const data = await res.json();

      // Check whether backend returns an array or an object with items/total
      if (Array.isArray(data)) {
        setRecords(data);
        setTotal(data.length);
      } else if (data && Array.isArray(data.items)) {
        setRecords(data.items);
        setTotal(data.total ?? data.items.length);
      } else {
        setRecords([]);
        setTotal(0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error fetching history';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sessionFilter, rangeFilter]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Trigger browser download of CSV directly from the backend endpoint
  const downloadCSV = useCallback(() => {
    const params = new URLSearchParams();
    params.set('format', 'csv');

    if (sessionFilter !== 'ALL') {
      params.set('session', sessionFilter);
    }

    const range = getISTDateRange(rangeFilter);
    if (range) {
      params.set('from', range.fromDate);
      params.set('to', range.toDate);
    }

    const downloadUrl = `/v1/silver?${params.toString()}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `silver999_history_${formatISTDateISO(new Date())}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [sessionFilter, rangeFilter]);

  return {
    records,
    loading,
    error,
    total,
    page,
    pageSize,
    sessionFilter,
    rangeFilter,
    setPage,
    setPageSize,
    setSessionFilter,
    setRangeFilter,
    downloadCSV,
    refresh: fetchHistory,
  };
}
