import React, { useState, useEffect } from 'react';
import { Activity, Clock, RefreshCw, Radio } from 'lucide-react';
import { SSEConnectionState, SchedulerMode, HealthStatus } from '../types';
import { Badge } from './ui/Badge';

interface HeaderProps {
  connectionState: SSEConnectionState;
  schedulerMode?: SchedulerMode;
  health?: HealthStatus | null;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  connectionState,
  schedulerMode = 'IDLE',
  health,
  onRefresh,
  isRefreshing = false,
}) => {
  const [istTime, setIstTime] = useState<string>('');

  // Live IST Clock ticking every second in Asia/Kolkata
  useEffect(() => {
    const updateTime = () => {
      try {
        const now = new Date();
        const formatted = new Intl.DateTimeFormat('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        }).format(now);
        setIstTime(formatted);
      } catch {
        setIstTime('--:--:--');
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getModeBadge = (mode: SchedulerMode) => {
    switch (mode) {
      case 'HOT':
        return {
          variant: 'coral' as const,
          label: 'HOT WINDOW',
          desc: 'High-frequency 30s poller active during publication window',
        };
      case 'CATCH_UP':
        return {
          variant: 'amber' as const,
          label: 'CATCH-UP',
          desc: '2m poller active — publication pending or delayed',
        };
      case 'OFF_DAY':
        return {
          variant: 'cream' as const,
          label: 'OFF-DAY',
          desc: 'Weekend / Government Holiday — 6h heartbeat poller',
        };
      case 'IDLE':
      default:
        return {
          variant: 'cream' as const,
          label: 'IDLE',
          desc: '15m maintenance poller — session captured',
        };
    }
  };

  const modeBadge = getModeBadge(schedulerMode);

  return (
    <header className="border-b border-claude-hairline bg-claude-canvas/95 backdrop-blur-sm sticky top-0 z-30 px-4 sm:px-8 py-3.5 transition-colors">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Brand & Wordmark (Claude Editorial Aesthetic) */}
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-claude-md bg-claude-primary/10 border border-claude-primary/20 flex items-center justify-center text-claude-primary">
            {/* Claude-style 4-spoke asterisk mark */}
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M12 2l1.5 6.5L20 10l-5.5 3.5L16 20l-4-4.5L8 20l1.5-6.5L4 10l6.5-1.5L12 2z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif text-xl font-normal tracking-tight text-claude-ink">
                SilverSurf
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-claude-primary" aria-hidden="true" />
              <span className="text-[11px] font-sans px-1.5 py-0.5 rounded bg-claude-surface-card text-claude-muted border border-claude-hairline">
                IBJA Benchmark
              </span>
            </div>
            <p className="text-[11px] font-sans text-claude-muted hidden md:block">
              India Bullion and Jewellers Association Silver 999 Monitor
            </p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex flex-wrap items-center justify-center sm:justify-end gap-2.5 text-xs font-sans">
          {/* Live SSE Status */}
          {connectionState === 'connected' && (
            <Badge variant="teal" dot pulse>
              <Radio className="h-3 w-3 inline mr-0.5" aria-hidden="true" />
              Live SSE Feed
            </Badge>
          )}
          {connectionState === 'connecting' && (
            <Badge variant="amber" dot pulse>
              Reconnecting
            </Badge>
          )}
          {connectionState === 'disconnected' && (
            <Badge variant="cream" dot>
              Offline
            </Badge>
          )}

          {/* Scheduler Mode */}
          <div title={modeBadge.desc} aria-label={modeBadge.desc} role="status" tabIndex={0} className="cursor-help rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-primary">
            <Badge variant={modeBadge.variant}>
              <Activity className="h-3 w-3 inline mr-0.5" aria-hidden="true" />
              Mode: {modeBadge.label}
            </Badge>
          </div>

          {/* Quarantined Count */}
          {health && health.quarantined_records_count > 0 && (
            <Badge variant="red" dot pulse>
              {health.quarantined_records_count} Quarantined
            </Badge>
          )}

          {/* Live IST Clock */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-claude-md bg-claude-surface-soft border border-claude-hairline text-claude-body font-mono text-[11px] tabular-nums">
            <Clock className="h-3.5 w-3.5 text-claude-muted" aria-hidden="true" />
            <span className="font-medium text-claude-ink">{istTime}</span>
            <span className="text-[10px] text-claude-muted font-sans uppercase">IST</span>
          </div>

          {/* Refresh Action */}
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing}
              aria-label="Refresh rates and status"
              aria-busy={isRefreshing}
              title="Refresh latest rate and status"
              className="p-1.5 min-h-[36px] min-w-[36px] inline-flex items-center justify-center rounded-claude-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-primary bg-claude-canvas border border-claude-hairline text-claude-muted hover:text-claude-primary hover:border-claude-primary/40 transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-claude-primary' : ''}`}
                aria-hidden="true"
              />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
