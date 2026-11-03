import React, { useState } from 'react';
import { Sparkles, CheckCircle2, History } from 'lucide-react';
import { SilverRate, RateUnit } from '../types';
import { formatINR, formatDate, formatISTTime } from '../utils/formatters';
import { calculateWithGST, convertRateUnit, getUnitDisplayLabel } from '../utils/calculations';
import { Badge } from './ui/Badge';
import { Toggle } from './ui/Toggle';
import { Button } from './ui/Button';

interface LiveRateCardProps {
  rate: SilverRate | null;
  loading?: boolean;
  isLiveFlash?: boolean;
  includeGst: boolean;
  onToggleGst: (value: boolean) => void;
}

export const LiveRateCard: React.FC<LiveRateCardProps> = ({
  rate,
  loading = false,
  isLiveFlash = false,
  includeGst,
  onToggleGst,
}) => {
  const [selectedUnit, setSelectedUnit] = useState<RateUnit>('per_kg');

  if (loading && !rate) {
    return (
      <div className="rounded-claude-lg border border-claude-hairline bg-claude-surface-card p-6 sm:p-8 animate-pulse shadow-claude-card">
        <div className="flex justify-between items-center mb-6">
          <div className="h-4 bg-claude-hairline rounded w-44" />
          <div className="h-6 bg-claude-hairline rounded-full w-20" />
        </div>
        <div className="h-16 bg-claude-hairline rounded w-64 mb-4" />
        <div className="h-4 bg-claude-hairline rounded w-48 mb-6" />
        <div className="h-10 bg-claude-hairline rounded w-full" />
      </div>
    );
  }

  const baseRatePerKg = rate?.price_inr_per_kg ?? 0;
  const effectiveBaseKg = includeGst ? calculateWithGST(baseRatePerKg) : baseRatePerKg;

  const activePrice = rate ? convertRateUnit(effectiveBaseKg, selectedUnit) : null;
  const activeDecimals = selectedUnit === 'per_gram' ? 3 : 2;

  const kgPrice = rate ? convertRateUnit(effectiveBaseKg, 'per_kg') : null;
  const tenGramPrice = rate ? convertRateUnit(effectiveBaseKg, 'per_10g') : null;
  const gramPrice = rate ? convertRateUnit(effectiveBaseKg, 'per_gram') : null;

  const isRevised = (rate?.revision ?? 1) > 1;

  return (
    <div
      className={`relative rounded-claude-lg border transition-all duration-300 bg-claude-surface-card p-6 sm:p-8 shadow-claude-card overflow-hidden ${
        isLiveFlash
          ? 'border-claude-primary ring-2 ring-claude-primary/20 bg-claude-surface-cream-strong'
          : 'border-claude-hairline hover:border-claude-muted-soft/40'
      }`}
    >
      {/* Top Header: Title & Badges */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-claude-hairline">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-sans font-medium tracking-wide text-claude-muted uppercase">
              Silver 999 Benchmark
            </h3>
            <span className="text-claude-muted-soft">•</span>
            <span className="text-xs font-sans text-claude-body">
              {rate ? formatDate(rate.rate_date) : 'Awaiting publication'}
            </span>
          </div>
          <p className="font-serif text-2xl sm:text-3xl text-claude-ink mt-0.5">
            Official Daily Benchmark Rate
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          {/* Session Pill */}
          {rate && (
            <Badge
              variant={rate.session === 'AM' ? 'teal' : 'coral'}
              className="text-xs font-medium px-3 py-1"
            >
              Session {rate.session}
            </Badge>
          )}

          {/* Revision Pill */}
          {rate && (
            <Badge
              variant={isRevised ? 'amber' : 'cream'}
              className="text-xs px-2.5 py-1"
            >
              {isRevised ? (
                <>
                  <History className="h-3 w-3 inline mr-1" aria-hidden="true" />
                  Rev {rate.revision} (Revised)
                </>
              ) : (
                `Rev ${rate.revision}`
              )}
            </Badge>
          )}

          {/* Derived GST indicator */}
          {includeGst && (
            <Badge variant="coral" className="text-xs">
              <Sparkles className="h-3 w-3 inline mr-1" aria-hidden="true" />
              +3% GST Derived
            </Badge>
          )}
        </div>
      </div>

      {/* Main Rate Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left Column: Big Price & Equivalents */}
        <div className="lg:col-span-7">
          <div className="flex items-baseline gap-2 sm:gap-3 flex-wrap" aria-live="polite" aria-atomic="true">
            <span className="font-serif text-4xl sm:text-5xl lg:text-6xl font-normal tracking-tight text-claude-ink tabular-nums">
              {formatINR(activePrice, activeDecimals)}
            </span>
            <span className="font-sans text-base sm:text-lg font-normal text-claude-muted">
              {getUnitDisplayLabel(selectedUnit)}
            </span>
          </div>

          {/* Secondary Units Row */}
          <div className="mt-3.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs font-sans text-claude-body">
            <div className="flex items-center gap-1.5">
              <span className="text-claude-muted font-normal">10g:</span>
              <span className="text-claude-ink font-mono font-medium tabular-nums">
                {formatINR(tenGramPrice, 2)}
              </span>
            </div>
            <span className="text-claude-hairline">•</span>
            <div className="flex items-center gap-1.5">
              <span className="text-claude-muted font-normal">1g:</span>
              <span className="text-claude-ink font-mono font-medium tabular-nums">
                {formatINR(gramPrice, 3)}
              </span>
            </div>
            <span className="text-claude-hairline">•</span>
            <div className="flex items-center gap-1.5">
              <span className="text-claude-muted font-normal">1kg:</span>
              <span className="text-claude-ink font-mono font-medium tabular-nums">
                {formatINR(kgPrice, 2)}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Unit Switcher & GST Toggle */}
        <div className="lg:col-span-5 flex flex-col sm:items-end gap-3.5 p-4 rounded-claude-md bg-claude-canvas border border-claude-hairline">
          {/* Unit Switcher */}
          <div className="w-full flex items-center justify-between sm:justify-end gap-2">
            <span className="text-xs font-sans text-claude-muted">Unit:</span>
            <div
              role="group"
              aria-label="Price unit selection"
              className="inline-flex rounded-claude-md p-0.5 bg-claude-surface-soft border border-claude-hairline"
            >
              <Button
                size="xs"
                variant="secondary"
                active={selectedUnit === 'per_kg'}
                aria-pressed={selectedUnit === 'per_kg'}
                onClick={() => setSelectedUnit('per_kg')}
              >
                ₹ / kg
              </Button>
              <Button
                size="xs"
                variant="secondary"
                active={selectedUnit === 'per_10g'}
                aria-pressed={selectedUnit === 'per_10g'}
                onClick={() => setSelectedUnit('per_10g')}
              >
                ₹ / 10g
              </Button>
              <Button
                size="xs"
                variant="secondary"
                active={selectedUnit === 'per_gram'}
                aria-pressed={selectedUnit === 'per_gram'}
                onClick={() => setSelectedUnit('per_gram')}
              >
                ₹ / g
              </Button>
            </div>
          </div>

          {/* GST Toggle Switch */}
          <div className="w-full flex items-center justify-between sm:justify-end gap-3 pt-2 border-t border-claude-hairline">
            <Toggle
              id="gst-toggle"
              checked={includeGst}
              onChange={onToggleGst}
              label="Include 3% GST"
              sublabel={includeGst ? 'Derived' : 'Excl.'}
            />
          </div>
        </div>
      </div>

      {/* Footer Info: Detection Timestamp */}
      <div className="mt-6 pt-4 border-t border-claude-hairline flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs font-sans text-claude-muted">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-claude-teal shrink-0" aria-hidden="true" />
          <span>
            Captured at:{' '}
            <strong className="text-claude-ink font-mono tabular-nums">
              {formatISTTime(rate?.detected_at)}
            </strong>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-claude-muted">
          <span>Source: {rate?.source ?? 'ibjarates.com'}</span>
          <span>•</span>
          <span className="text-claude-body font-medium">Verified Clean</span>
        </div>
      </div>
    </div>
  );
};
