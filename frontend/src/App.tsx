import React, { useMemo, useState } from 'react';
import { Header } from './components/Header';
import { LiveRateCard } from './components/LiveRateCard';
import { StalenessBanner } from './components/StalenessBanner';
import { TrendChart } from './components/TrendChart';
import { HistoryTable } from './components/HistoryTable';
import { Attribution } from './components/Attribution';
import {
  useLatestRate,
  useRateStream,
  useRateHistory,
  useHealthStatus,
} from './hooks';
import { calculateWithGST } from './utils/calculations';

export const App: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [includeGst, setIncludeGst] = useState(false);

  // 1. Live SSE Rate Stream
  const { connectionState, reconnect } = useRateStream({
    onEvent: (event) => {
      handleStreamEvent(event);
      refreshHistory();
    },
  });

  // 2. Latest Rate Hook
  const {
    rate,
    loading: rateLoading,
    error: rateError,
    refresh: refreshLatest,
    handleStreamEvent,
    isLiveFlash,
  } = useLatestRate();

  // 3. Operational Health & Scheduler Hook
  const {
    health,
    refresh: refreshHealth,
  } = useHealthStatus({ pollingIntervalMs: 15000 });

  // 4. Historical Rates Hook
  const {
    records,
    loading: historyLoading,
    sessionFilter,
    rangeFilter,
    page,
    pageSize,
    total,
    setPage,
    setSessionFilter,
    setRangeFilter,
    downloadCSV,
    refresh: refreshHistory,
  } = useRateHistory();

  // Unified manual refresh
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await Promise.allSettled([
      refreshLatest(),
      refreshHealth(),
      refreshHistory(),
    ]);
    reconnect();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const displayRate = rate;
  const displayRecords = useMemo(
    () =>
      includeGst
        ? records.map((r) => ({
            ...r,
            price_inr: calculateWithGST(r.price_inr),
            price_inr_per_kg: calculateWithGST(r.price_inr_per_kg ?? r.price_inr),
            price_inr_per_10g: calculateWithGST(r.price_inr_per_10g ?? r.price_inr / 100),
          }))
        : records,
    [records, includeGst]
  );

  return (
    <div className="min-h-screen bg-claude-canvas text-claude-ink flex flex-col font-sans selection:bg-claude-primary/20 selection:text-claude-primary">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:rounded-claude-md focus:bg-claude-primary focus:text-white"
      >
        Skip to main content
      </a>

      {/* Top Navigation */}
      <Header
        connectionState={connectionState}
        schedulerMode={health?.scheduler_mode || 'HOT'}
        health={health}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Container */}
      <main id="main-content" className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 space-y-8">
        {/* Editorial Sub-hero Introduction */}
        <div className="pb-2">
          <h1 className="font-serif text-3xl sm:text-4xl text-claude-ink font-normal tracking-tight">
            India Bullion Benchmark
          </h1>
          <p className="text-sm font-sans text-claude-muted mt-1.5 max-w-2xl">
            Real-time Silver 999 opening and closing benchmark quotes from Mumbai physical markets.
          </p>
        </div>

        {/* Offline Notice when backend server is unreachable */}
        {rateError && (
          <div className="rounded-claude-md border border-claude-hairline bg-claude-surface-soft p-3.5 text-xs font-sans text-claude-body flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-claude-amber" aria-hidden="true" />
              <span>
                Backend API not detected at <code className="px-1 py-0.5 rounded bg-claude-surface-card text-claude-ink font-mono border border-claude-hairline">http://localhost:8000</code>. No rate data is available until the backend is reachable.
              </span>
            </span>
            <button
              type="button"
              onClick={handleManualRefresh}
              className="text-claude-primary hover:text-claude-primary-active underline underline-offset-2 cursor-pointer ml-3 font-medium shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-primary rounded"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Staleness Banner */}
        {displayRate && (
          <StalenessBanner
            stale={displayRate.stale}
            staleReason={displayRate.stale_reason}
            nextExpectedPublication={displayRate.next_expected_publication}
          />
        )}

        {/* Hero Section: Live Rate Card */}
        <section aria-labelledby="live-rate-section">
          <h2 id="live-rate-section" className="sr-only">
            Live Benchmark Rate Card
          </h2>
          <LiveRateCard
            rate={displayRate}
            loading={rateLoading && !displayRate}
            isLiveFlash={isLiveFlash}
            includeGst={includeGst}
            onToggleGst={setIncludeGst}
          />
        </section>

        {/* Trend Chart Section (Claude Dark Product Chrome) */}
        <section aria-labelledby="trend-section">
          <h2 id="trend-section" className="sr-only">
            Benchmark Price Trajectory
          </h2>
          <TrendChart
            records={displayRecords}
            loading={historyLoading && records.length === 0}
            selectedRange={rangeFilter}
            onRangeChange={setRangeFilter}
            includeGst={includeGst}
          />
        </section>

        {/* History Table Section */}
        <section aria-labelledby="history-section">
          <h2 id="history-section" className="sr-only">
            Historical Benchmark Archive
          </h2>
          <HistoryTable
            records={displayRecords}
            loading={historyLoading && records.length === 0}
            sessionFilter={sessionFilter}
            onSessionFilterChange={setSessionFilter}
            onExportCSV={downloadCSV}
            total={total || displayRecords.length}
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            includeGst={includeGst}
          />
        </section>
      </main>

      {/* Claude Style Dark Navy Footer */}
      <Attribution />
    </div>
  );
};

export default App;
