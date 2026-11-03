import React, { useState, useMemo } from 'react';
import { Download, ChevronLeft, ChevronRight, ArrowUpDown, Database, AlertCircle } from 'lucide-react';
import { HistoricalRateRecord, SessionType } from '../types';
import { formatINR, formatDate } from '../utils/formatters';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';

interface HistoryTableProps {
  records: HistoricalRateRecord[];
  loading?: boolean;
  sessionFilter: SessionType | 'ALL';
  onSessionFilterChange: (session: SessionType | 'ALL') => void;
  onExportCSV: () => void;
  total?: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  includeGst?: boolean;
}

type SortField = 'date' | 'price' | 'session';
type SortOrder = 'asc' | 'desc';

export const HistoryTable: React.FC<HistoryTableProps> = ({
  records,
  loading = false,
  sessionFilter,
  onSessionFilterChange,
  onExportCSV,
  total,
  page,
  pageSize,
  onPageChange,
  includeGst = false,
}) => {
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const sortedRecords = useMemo(() => {
    return [...records].sort((a, b) => {
      let comparison = 0;
      if (sortField === 'date') {
        comparison = a.rate_date.localeCompare(b.rate_date);
        if (comparison === 0) {
          comparison = a.session.localeCompare(b.session);
        }
      } else if (sortField === 'price') {
        const pA = a.price_inr_per_kg ?? a.price_inr;
        const pB = b.price_inr_per_kg ?? b.price_inr;
        comparison = pA - pB;
      } else if (sortField === 'session') {
        comparison = a.session.localeCompare(b.session);
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [records, sortField, sortOrder]);

  const effectiveTotal = total ?? records.length;
  const totalPages = Math.max(1, Math.ceil(effectiveTotal / pageSize));

  return (
    <div className="rounded-claude-lg border border-claude-hairline bg-claude-surface-card shadow-claude-card overflow-hidden">
      {/* Table Toolbar Header */}
      <div className="p-5 border-b border-claude-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-claude-canvas/60">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-claude-sm bg-claude-surface-soft border border-claude-hairline text-claude-primary">
            <Database className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-base font-serif font-normal tracking-tight text-claude-ink">
              Historical Rates Archive
            </h3>
            <p className="text-xs font-sans text-claude-muted">
              Published IBJA Silver 999 Benchmark Sessions
            </p>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Session Filter */}
          <div
            role="group"
            aria-label="Filter by session"
            className="inline-flex rounded-claude-md p-0.5 bg-claude-surface-soft border border-claude-hairline"
          >
            {(['ALL', 'AM', 'PM'] as const).map((s) => (
              <Button
                key={s}
                size="xs"
                variant="secondary"
                active={sessionFilter === s}
                aria-pressed={sessionFilter === s}
                onClick={() => onSessionFilterChange(s)}
              >
                {s === 'ALL' ? 'All Sessions' : s}
              </Button>
            ))}
          </div>

          {/* Export CSV Button (Claude Coral Primary) */}
          <Button
            size="xs"
            variant="primary"
            icon={<Download className="h-3.5 w-3.5 text-white" aria-hidden="true" />}
            onClick={onExportCSV}
            title="Download historical rates as CSV"
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Table Responsive Wrapper */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs font-sans">
          <thead>
            <tr className="border-b border-claude-hairline bg-claude-surface-soft text-claude-muted">
              <th
                scope="col"
                aria-sort={sortField === 'date' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
                className="py-3 px-4 font-medium select-none"
              >
                <button
                  type="button"
                  className="flex items-center gap-1.5 font-medium text-claude-muted hover:text-claude-ink transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-claude-primary rounded px-1 -mx-1 cursor-pointer"
                  onClick={() => handleSort('date')}
                >
                  <span>Rate Date</span>
                  <ArrowUpDown className="h-3 w-3 text-claude-muted-soft" aria-hidden="true" />
                </button>
              </th>
              <th
                scope="col"
                aria-sort={sortField === 'session' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
                className="py-3 px-4 font-medium select-none"
              >
                <button
                  type="button"
                  className="flex items-center gap-1.5 font-medium text-claude-muted hover:text-claude-ink transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-claude-primary rounded px-1 -mx-1 cursor-pointer"
                  onClick={() => handleSort('session')}
                >
                  <span>Session</span>
                  <ArrowUpDown className="h-3 w-3 text-claude-muted-soft" aria-hidden="true" />
                </button>
              </th>
              <th
                scope="col"
                aria-sort={sortField === 'price' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
                className="py-3 px-4 font-medium select-none"
              >
                <button
                  type="button"
                  className="flex items-center gap-1.5 font-medium text-claude-muted hover:text-claude-ink transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-claude-primary rounded px-1 -mx-1 cursor-pointer"
                  onClick={() => handleSort('price')}
                >
                  <span>Benchmark Rate (₹){includeGst ? ' +3% GST' : ''}</span>
                  <ArrowUpDown className="h-3 w-3 text-claude-muted-soft" aria-hidden="true" />
                </button>
              </th>
              <th scope="col" className="py-3 px-4 font-medium">
                10g Equivalent
              </th>
              <th scope="col" className="py-3 px-4 font-medium">
                Unit
              </th>
              <th scope="col" className="py-3 px-4 font-medium">
                Status
              </th>
              <th scope="col" className="py-3 px-4 font-medium">
                Revision
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-claude-hairline/80 bg-white/40">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-claude-muted">
                  <div className="inline-flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-claude-primary animate-ping" />
                    <span>Loading historical records…</span>
                  </div>
                </td>
              </tr>
            ) : sortedRecords.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-claude-muted">
                  <div className="flex flex-col items-center justify-center gap-1">
                    <AlertCircle className="h-5 w-5 text-claude-muted-soft mb-1" aria-hidden="true" />
                    <span>No records found for current filters</span>
                  </div>
                </td>
              </tr>
            ) : (
              sortedRecords.map((r, index) => {
                const price = r.price_inr_per_kg ?? r.price_inr;
                const tenGramPrice = r.price_inr_per_10g ?? price / 100;
                const isQuarantined = r.status === 'quarantined';
                const isSuperseded = r.status === 'superseded';

                return (
                  <tr
                    key={`${r.rate_date}-${r.session}-${r.revision || index}`}
                    className={`transition-colors hover:bg-claude-surface-soft/60 ${
                      isSuperseded ? 'opacity-60 bg-claude-surface-soft/30' : ''
                    } ${isQuarantined ? 'bg-red-50/50' : ''}`}
                  >
                    <td className="py-3 px-4 text-claude-ink font-medium whitespace-nowrap">
                      {formatDate(r.rate_date)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <Badge
                        variant={r.session === 'AM' ? 'teal' : 'coral'}
                        className="text-[11px]"
                      >
                        {r.session}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-semibold text-claude-ink font-mono tabular-nums whitespace-nowrap">
                      {formatINR(price, 2)}
                    </td>
                    <td className="py-3 px-4 text-claude-body font-mono tabular-nums whitespace-nowrap">
                      {formatINR(tenGramPrice, 2)}
                    </td>
                    <td className="py-3 px-4 text-claude-muted whitespace-nowrap">
                      {r.unit || 'per_kg'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {isQuarantined ? (
                        <Badge variant="red">Quarantined</Badge>
                      ) : isSuperseded ? (
                        <Badge variant="cream">Superseded</Badge>
                      ) : (
                        <Badge variant="teal">Valid</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 text-claude-muted whitespace-nowrap">
                      <span className="inline-block px-1.5 py-0.5 rounded bg-claude-surface-soft text-[11px] font-mono border border-claude-hairline">
                        v{r.revision || 1}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3.5 sm:px-5 border-t border-claude-hairline flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-sans text-claude-muted bg-claude-canvas/60">
        <div>
          Showing{' '}
          <strong className="text-claude-ink font-mono tabular-nums">
            {records.length > 0 ? (page - 1) * pageSize + 1 : 0}
          </strong>{' '}
          to{' '}
          <strong className="text-claude-ink font-mono tabular-nums">
            {Math.min(page * pageSize, effectiveTotal)}
          </strong>{' '}
          of <strong className="text-claude-ink font-mono tabular-nums">{effectiveTotal}</strong> records
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="xs"
            variant="secondary"
            disabled={page <= 1 || loading}
            onClick={() => onPageChange(page - 1)}
            icon={<ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />}
          >
            Prev
          </Button>
          <span className="px-2 text-claude-body">
            Page {page} of {totalPages}
          </span>
          <Button
            size="xs"
            variant="secondary"
            disabled={page >= totalPages || loading}
            onClick={() => onPageChange(page + 1)}
            icon={<ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};
