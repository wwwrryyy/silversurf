import { useState, useEffect, useCallback, useRef } from 'react';
import { SilverRate, SSERateEvent } from '../types';

interface UseLatestRateOptions {
  includeGst?: boolean;
  onNewRate?: (rate: SilverRate) => void;
}

export function useLatestRate({
  includeGst = false,
  onNewRate,
}: UseLatestRateOptions = {}) {
  const [rate, setRate] = useState<SilverRate | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isLiveFlash, setIsLiveFlash] = useState<boolean>(false);
  const flashTimeoutRef = useRef<number | null>(null);

  const fetchLatest = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const url = `/v1/silver/latest?include_gst=${includeGst}`;
      const response = await fetch(url, {
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch latest rate: HTTP ${response.status}`);
      }

      const data: SilverRate = await response.json();
      setRate(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error fetching rate';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [includeGst]);

  // Initial fetch and on includeGst change
  useEffect(() => {
    fetchLatest();
  }, [fetchLatest]);

  // Handle incoming live SSE event
  const handleStreamEvent = useCallback(
    (event: SSERateEvent) => {
      if (event.event === 'rate.published' || event.event === 'rate.revised') {
        const incomingRate = event.data;
        setRate(incomingRate);
        onNewRate?.(incomingRate);

        // Trigger flash indicator for 1.5 seconds
        setIsLiveFlash(true);
        if (flashTimeoutRef.current) {
          window.clearTimeout(flashTimeoutRef.current);
        }
        flashTimeoutRef.current = window.setTimeout(() => {
          setIsLiveFlash(false);
        }, 1500);
      }
    },
    [onNewRate]
  );

  useEffect(() => {
    return () => {
      if (flashTimeoutRef.current) {
        window.clearTimeout(flashTimeoutRef.current);
      }
    };
  }, []);

  return {
    rate,
    loading,
    error,
    refresh: fetchLatest,
    handleStreamEvent,
    isLiveFlash,
  };
}
