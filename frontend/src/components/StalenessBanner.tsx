import React from 'react';
import { AlertTriangle, Calendar, Info } from 'lucide-react';
import { StaleReason } from '../types';
import { formatISTDateTime } from '../utils/formatters';

interface StalenessBannerProps {
  stale: boolean;
  staleReason?: StaleReason;
  nextExpectedPublication?: string | null;
  className?: string;
}

export const StalenessBanner: React.FC<StalenessBannerProps> = ({
  stale,
  staleReason,
  nextExpectedPublication,
  className = '',
}) => {
  if (!stale && !nextExpectedPublication) {
    return null;
  }

  const getReasonText = (reason: StaleReason | undefined) => {
    switch (reason) {
      case 'not_yet_published':
        return 'The publication window for this session has ended, but IBJA has not published the new rate yet. Displaying previously verified rate.';
      case 'parser_unhealthy':
        return 'Layout Verification Notice: SilverSurf detected a structural divergence on ibjarates.com. Displaying last verified rate.';
      case 'source_unavailable':
        return 'IBJA website was unreachable during the polling window. Engine is actively retrying in catch-up mode.';
      default:
        return 'Benchmark rate may not reflect today’s current trading session.';
    }
  };

  if (stale) {
    return (
      <div
        role="alert"
        className={`rounded-claude-md border border-claude-amber/40 bg-claude-amber/10 p-3.5 text-[#8f5615] font-sans text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 shadow-xs ${className}`}
      >
        <div className="flex items-start sm:items-center gap-2.5">
          <AlertTriangle className="h-4 w-4 text-claude-amber shrink-0 mt-0.5 sm:mt-0" aria-hidden="true" />
          <div>
            <span className="font-semibold text-claude-ink mr-2">
              Publication Pending:
            </span>
            <span>{getReasonText(staleReason)}</span>
          </div>
        </div>

        {nextExpectedPublication && (
          <div className="flex items-center gap-1.5 text-claude-body shrink-0 text-[11px] bg-white/70 px-2.5 py-1 rounded-claude-sm border border-claude-hairline">
            <Calendar className="h-3 w-3 text-claude-muted" aria-hidden="true" />
            <span>Next Window: {formatISTDateTime(nextExpectedPublication)}</span>
          </div>
        )}
      </div>
    );
  }

  if (nextExpectedPublication) {
    return (
      <div className={`rounded-claude-md border border-claude-hairline bg-claude-surface-card p-3 text-claude-body font-sans text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 ${className}`}>
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-claude-primary shrink-0" aria-hidden="true" />
          <span>Non-trading period (weekend or central government holiday). Current benchmark rate remains official until next business session.</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-claude-muted shrink-0 font-mono">
          <Calendar className="h-3 w-3 text-claude-muted-soft" aria-hidden="true" />
          <span>Next Expected: {formatISTDateTime(nextExpectedPublication)}</span>
        </div>
      </div>
    );
  }

  return null;
};
