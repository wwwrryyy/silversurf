import { useState, useEffect, useCallback } from 'react';
import { HealthStatus } from '../types';

interface UseHealthStatusOptions {
  pollingIntervalMs?: number;
  enabled?: boolean;
}

export function useHealthStatus({
  pollingIntervalMs = 15000, // Poll every 15 seconds
  enabled = true,
}: UseHealthStatusOptions = {}) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    if (!enabled) return;

    try {
      const res = await fetch('/v1/health', {
        headers: { Accept: 'application/json' },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: HealthStatus = await res.json();
      setHealth(data);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch health status';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    fetchHealth();

    if (!enabled || pollingIntervalMs <= 0) return;

    const intervalId = window.setInterval(fetchHealth, pollingIntervalMs);
    return () => window.clearInterval(intervalId);
  }, [fetchHealth, enabled, pollingIntervalMs]);

  return {
    health,
    loading,
    error,
    refresh: fetchHealth,
  };
}
