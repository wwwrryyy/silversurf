import React, { useState, useMemo } from 'react';
import { TrendingUp } from 'lucide-react';
import { HistoricalRateRecord } from '../types';
import { formatINR, formatDate } from '../utils/formatters';
import { Button } from './ui/Button';

interface TrendChartProps {
  records: HistoricalRateRecord[];
  loading?: boolean;
  selectedRange: '7D' | '30D' | '90D' | 'ALL';
  onRangeChange: (range: '7D' | '30D' | '90D' | 'ALL') => void;
  includeGst?: boolean;
}

interface DatePoint {
  date: string;
  amPrice: number | null;
  pmPrice: number | null;
  latestPrice: number;
}

export const TrendChart: React.FC<TrendChartProps> = ({
  records,
  loading = false,
  selectedRange,
  onRangeChange,
  includeGst = false,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Group and sort data points by date ascending
  const chartPoints = useMemo<DatePoint[]>(() => {
    if (!records || records.length === 0) return [];

    const map = new Map<string, { am: number | null; pm: number | null }>();

    records.forEach((r) => {
      if (r.status === 'quarantined') return;
      const existing = map.get(r.rate_date) || { am: null, pm: null };
      const price = r.price_inr_per_kg ?? r.price_inr;

      if (r.session === 'AM') {
        existing.am = price;
      } else if (r.session === 'PM') {
        existing.pm = price;
      }
      map.set(r.rate_date, existing);
    });

    const dates = Array.from(map.keys()).sort();

    return dates.map((date) => {
      const data = map.get(date)!;
      const latestPrice = data.pm ?? data.am ?? 0;
      return {
        date,
        amPrice: data.am,
        pmPrice: data.pm,
        latestPrice,
      };
    });
  }, [records]);

  // Compute bounds
  const { minPrice, priceRange } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;

    chartPoints.forEach((p) => {
      if (p.amPrice !== null) {
        if (p.amPrice < min) min = p.amPrice;
        if (p.amPrice > max) max = p.amPrice;
      }
      if (p.pmPrice !== null) {
        if (p.pmPrice < min) min = p.pmPrice;
        if (p.pmPrice > max) max = p.pmPrice;
      }
    });

    if (min === Infinity || max === -Infinity) {
      return { minPrice: 90000, maxPrice: 100000, priceRange: 10000 };
    }

    const margin = Math.max((max - min) * 0.04, 500);
    const paddedMin = Math.floor((min - margin) / 500) * 500;
    const paddedMax = Math.ceil((max + margin) / 500) * 500;

    return {
      minPrice: paddedMin,
      maxPrice: paddedMax,
      priceRange: paddedMax - paddedMin || 1,
    };
  }, [chartPoints]);

  const svgWidth = 800;
  const svgHeight = 280;
  const padding = { top: 20, right: 20, bottom: 40, left: 75 };
  const innerWidth = svgWidth - padding.left - padding.right;
  const innerHeight = svgHeight - padding.top - padding.bottom;

  const getX = (index: number) => {
    if (chartPoints.length <= 1) return padding.left + innerWidth / 2;
    return padding.left + (index / (chartPoints.length - 1)) * innerWidth;
  };

  const getY = (val: number) => {
    const ratio = (val - minPrice) / priceRange;
    return padding.top + innerHeight - ratio * innerHeight;
  };

  const amPathData = useMemo(() => {
    const points: string[] = [];
    chartPoints.forEach((p, idx) => {
      if (p.amPrice !== null) {
        points.push(`${getX(idx).toFixed(1)},${getY(p.amPrice).toFixed(1)}`);
      }
    });
    return points.length > 0 ? `M ${points.join(' L ')}` : '';
  }, [chartPoints, minPrice, priceRange]);

  const pmPathData = useMemo(() => {
    const points: string[] = [];
    chartPoints.forEach((p, idx) => {
      if (p.pmPrice !== null) {
        points.push(`${getX(idx).toFixed(1)},${getY(p.pmPrice).toFixed(1)}`);
      }
    });
    return points.length > 0 ? `M ${points.join(' L ')}` : '';
  }, [chartPoints, minPrice, priceRange]);

  const areaGradientPath = useMemo(() => {
    if (chartPoints.length === 0) return '';
    const points: string[] = [];
    chartPoints.forEach((p, idx) => {
      points.push(`${getX(idx).toFixed(1)},${getY(p.latestPrice).toFixed(1)}`);
    });
    const firstX = getX(0).toFixed(1);
    const lastX = getX(chartPoints.length - 1).toFixed(1);
    const bottomY = (padding.top + innerHeight).toFixed(1);
    return `M ${firstX},${bottomY} L ${points.join(' L ')} L ${lastX},${bottomY} Z`;
  }, [chartPoints, minPrice, priceRange]);

  const yTicks = useMemo(() => {
    const ticks = [];
    const count = 4;
    for (let i = 0; i <= count; i++) {
      const val = minPrice + (priceRange * i) / count;
      const y = padding.top + innerHeight - (i / count) * innerHeight;
      ticks.push({ val, y });
    }
    return ticks;
  }, [minPrice, priceRange]);

  const xLabelIndices = useMemo(() => {
    if (chartPoints.length <= 6) {
      return chartPoints.map((_, i) => i);
    }
    const step = Math.ceil(chartPoints.length / 5);
    const indices = [];
    for (let i = 0; i < chartPoints.length; i += step) {
      indices.push(i);
    }
    if (indices[indices.length - 1] !== chartPoints.length - 1) {
      indices.push(chartPoints.length - 1);
    }
    return indices;
  }, [chartPoints]);

  const activePoint = hoveredIndex !== null ? chartPoints[hoveredIndex] : null;

  return (
    <div className="rounded-claude-lg border border-white/10 bg-claude-surface-dark p-6 sm:p-7 shadow-claude-dark text-claude-on-dark">
      {/* Chart Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-claude-sm bg-white/5 border border-white/10 text-claude-primary">
            <TrendingUp className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-base font-serif font-normal tracking-normal text-white">
              Benchmark Rate History
            </h3>
            <p className="text-xs font-sans text-claude-on-dark-soft">
              Daily Opening (AM) and Closing (PM) Price Curves{includeGst ? ' · incl. 3% GST' : ''}
            </p>
          </div>
        </div>

        {/* Range Buttons & Legend */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Legend */}
          <div className="flex items-center gap-3.5 text-xs font-sans mr-2">
            <span className="flex items-center gap-1.5 text-claude-on-dark-soft">
              <span className="h-2 w-2.5 rounded-full bg-claude-teal inline-block" />
              AM (Open)
            </span>
            <span className="flex items-center gap-1.5 text-claude-on-dark-soft">
              <span className="h-2 w-2.5 rounded-full bg-claude-primary inline-block" />
              PM (Close)
            </span>
          </div>

          {/* Range Selector */}
          <div
            role="group"
            aria-label="Historical time range"
            className="inline-flex rounded-claude-md p-0.5 bg-claude-surface-dark-elevated border border-white/10"
          >
            {(['7D', '30D', '90D', 'ALL'] as const).map((range) => (
              <Button
                key={range}
                size="xs"
                variant="dark"
                active={selectedRange === range}
                aria-pressed={selectedRange === range}
                onClick={() => onRangeChange(range)}
              >
                {range}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* SVG Chart Canvas */}
      <div className="relative w-full overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-claude-surface-dark/80 backdrop-blur-xs flex items-center justify-center z-10">
            <span className="text-xs font-sans text-claude-on-dark-soft animate-pulse">
              Updating historical trend…
            </span>
          </div>
        )}

        {chartPoints.length === 0 && !loading ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-claude-on-dark-soft font-sans text-xs">
            <p>No rate records found for the selected {selectedRange} range.</p>
            <p className="text-[11px] mt-1 text-white/40">
              Historical records will populate as sessions are recorded.
            </p>
          </div>
        ) : (
          <div className="w-full">
            <svg
              role="group"
              tabIndex={0}
              aria-label="Silver 999 daily benchmark rate trend chart. Use left and right arrow keys to inspect values."
              onFocus={() => setHoveredIndex((i) => i ?? chartPoints.length - 1)}
              onBlur={() => setHoveredIndex(null)}
              onKeyDown={(e) => {
                if (chartPoints.length === 0) return;
                if (e.key === 'ArrowLeft') {
                  e.preventDefault();
                  setHoveredIndex((i) => Math.max(0, (i ?? chartPoints.length) - 1));
                } else if (e.key === 'ArrowRight') {
                  e.preventDefault();
                  setHoveredIndex((i) => Math.min(chartPoints.length - 1, (i ?? -1) + 1));
                } else if (e.key === 'Escape') {
                  setHoveredIndex(null);
                }
              }}
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-auto overflow-visible select-none"
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <defs>
                <linearGradient id="claudeAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#cc785c" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#cc785c" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Horizontal Grid lines & Y-Axis Ticks */}
              {yTicks.map((tick, i) => (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={tick.y}
                    x2={svgWidth - padding.right}
                    y2={tick.y}
                    stroke="#252320"
                    strokeWidth="1"
                    strokeDasharray="2 3"
                  />
                  <text
                    x={padding.left - 8}
                    y={tick.y + 4}
                    textAnchor="end"
                    className="text-[10px] fill-claude-on-dark-soft font-mono tabular-nums"
                  >
                    {formatINR(tick.val, 0)}
                  </text>
                </g>
              ))}

              {/* Area fill */}
              {areaGradientPath && (
                <path d={areaGradientPath} fill="url(#claudeAreaGradient)" />
              )}

              {/* AM Rate Line (Claude Teal) */}
              {amPathData && (
                <path
                  d={amPathData}
                  fill="none"
                  stroke="#5db8a6"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* PM Rate Line (Claude Coral) */}
              {pmPathData && (
                <path
                  d={pmPathData}
                  fill="none"
                  stroke="#cc785c"
                  strokeWidth="2.4"
                  strokeDasharray="4 2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* Data points for AM */}
              {chartPoints.map((p, idx) => {
                if (p.amPrice === null) return null;
                const cx = getX(idx);
                const cy = getY(p.amPrice);
                const isHovered = hoveredIndex === idx;
                return (
                  <circle
                    key={`am-${idx}`}
                    cx={cx}
                    cy={cy}
                    r={isHovered ? 4.5 : 2.5}
                    fill="#5db8a6"
                    stroke="#181715"
                    strokeWidth="1.5"
                    className="transition-all duration-150"
                  />
                );
              })}

              {/* Data points for PM */}
              {chartPoints.map((p, idx) => {
                if (p.pmPrice === null) return null;
                const cx = getX(idx);
                const cy = getY(p.pmPrice);
                const isHovered = hoveredIndex === idx;
                return (
                  <circle
                    key={`pm-${idx}`}
                    cx={cx}
                    cy={cy}
                    r={isHovered ? 4.5 : 2.5}
                    fill="#cc785c"
                    stroke="#181715"
                    strokeWidth="1.5"
                    className="transition-all duration-150"
                  />
                );
              })}

              {/* X-Axis Dates */}
              {xLabelIndices.map((idx) => {
                const p = chartPoints[idx];
                if (!p) return null;
                const x = getX(idx);
                return (
                  <text
                    key={`label-${idx}`}
                    x={x}
                    y={svgHeight - 12}
                    textAnchor="middle"
                    className="text-[10px] fill-claude-on-dark-soft font-sans"
                  >
                    {formatDate(p.date)}
                  </text>
                );
              })}

              {/* Hover Crosshair & Interactive overlay */}
              {chartPoints.map((_, idx) => {
                const x = getX(idx);
                const width = innerWidth / (chartPoints.length || 1);
                return (
                  <rect
                    key={`hover-zone-${idx}`}
                    x={x - width / 2}
                    y={padding.top}
                    width={width}
                    height={innerHeight}
                    fill="transparent"
                    aria-hidden="true"
                    className="cursor-crosshair"
                    onMouseEnter={() => setHoveredIndex(idx)}
                    onPointerDown={() => setHoveredIndex(idx)}
                  />
                );
              })}

              {/* Active Crosshair Line */}
              {hoveredIndex !== null && (
                <line
                  x1={getX(hoveredIndex)}
                  y1={padding.top}
                  x2={getX(hoveredIndex)}
                  y2={padding.top + innerHeight}
                  stroke="#55524c"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                  className="pointer-events-none"
                />
              )}
            </svg>

            {/* Hover Tooltip Overlay */}
            {activePoint && hoveredIndex !== null && (
              <div
                className="absolute z-20 pointer-events-none bg-claude-surface-dark-elevated border border-white/15 rounded-claude-md p-3 shadow-claude-elevated text-xs font-sans text-claude-on-dark"
                style={{
                  top: '10px',
                  left: `${Math.min(
                    Math.max((hoveredIndex / (chartPoints.length - 1)) * 100, 10),
                    85
                  )}%`,
                  transform: 'translateX(-50%)',
                }}
              >
                <div className="font-serif text-sm text-white border-b border-white/10 pb-1 mb-1.5">
                  {formatDate(activePoint.date)}
                </div>
                <div className="space-y-1 font-mono text-[11px]">
                  <div className="flex items-center justify-between gap-4 text-claude-teal">
                    <span className="flex items-center gap-1 font-sans">
                      <span className="h-1.5 w-1.5 rounded-full bg-claude-teal" />
                      AM:
                    </span>
                    <span className="tabular-nums font-semibold">
                      {activePoint.amPrice ? formatINR(activePoint.amPrice, 2) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4 text-claude-primary">
                    <span className="flex items-center gap-1 font-sans">
                      <span className="h-1.5 w-1.5 rounded-full bg-claude-primary" />
                      PM:
                    </span>
                    <span className="tabular-nums font-semibold">
                      {activePoint.pmPrice ? formatINR(activePoint.pmPrice, 2) : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
