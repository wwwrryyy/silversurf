# Graph Report - silversurf  (2026-11-03)

## Corpus Check
- 72 files · ~25,246 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .conf 1, .css 1)

## Summary
- 585 nodes · 1300 edges · 48 communities (31 shown, 17 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 148 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- IbjaHtmlSource
- AdaptiveScheduler
- get_connection
- package.json
- test_scheduler.py
- AGENTS.md — SilverSurf Project Guide
- Session
- compilerOptions
- App.tsx
- LiveRateCard.tsx
- Header.tsx
- HistoryTable.tsx
- PRD: SilverSurf (IBJA Silver Rate Scraper & Live Feed)
- silver.ts
- react
- architecture.md
- Part I: Backend Architecture
- compilerOptions
- RateSource
- RawScrapeResult
- 6. Scope: Functional Requirements
- Notifier
- SSEEventBus
- engine.py
- silversurf-backend
- useRateHistory.ts
- silver.py
- schemas.py
- RateRepository
- RateRecord
- approve_quarantined_silver
- StalenessBanner.tsx
- test_parser.py
- 7. REST & SSE API Specification
- SilverSurf Architecture Document
- parse_dd_mm_yyyy_ist

## God Nodes (most connected - your core abstractions)
1. `RawScrapeResult` - 35 edges
2. `RateRepository` - 32 edges
3. `Session` - 31 edges
4. `AdaptiveScheduler` - 30 edges
5. `IbjaHtmlSource` - 30 edges
6. `get_connection()` - 29 edges
7. `Metal` - 22 edges
8. `RateRecord` - 20 edges
9. `RateStatus` - 19 edges
10. `IbjaPdfBackfillSource` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Core Architecture Principles` --references--> `RateSource`  [INFERRED]
  architecture.md → backend/app/sources/base.py
- `4. Validation Rules (V1–V5)` --references--> `ValidationPipeline`  [INFERRED]
  architecture.md → backend/app/validation/rules.py
- `4.3 `useRateHistory`` --references--> `useRateHistory()`  [INFERRED]
  architecture.md → frontend/src/hooks/useRateHistory.ts
- `2. Ingestion Pipeline & The `RateSource` Abstraction` --references--> `RateSource`  [INFERRED]
  architecture.md → backend/app/sources/base.py
- `11. Legal, Compliance & Risk (gate for launch)` --references--> `RateSource`  [INFERRED]
  PRD.md → backend/app/sources/base.py

## Import Cycles
- None detected.

## Communities (48 total, 17 thin omitted)

### Community 0 - "IbjaHtmlSource"
Cohesion: 0.10
Nodes (5): 2.1 Extraction Strategy (`IbjaHtmlSource`), IbjaHtmlSource, PlaywrightFallbackSource, test_ibja_html_source_shifted_columns(), test_ibja_html_source_unified_am_pm_columns()

### Community 1 - "AdaptiveScheduler"
Cohesion: 0.06
Nodes (8): lifespan(), root(), AdaptiveScheduler, init_db(), SnapshotManager, temp_env(), temp_storage(), test_snapshot_save_read_and_prune()

### Community 2 - "get_connection"
Cohesion: 0.21
Nodes (10): get_connection(), client(), setup_test_db(), test_date_endpoint(), test_health_and_metrics_endpoints(), test_latest_endpoint_empty_and_populated(), test_latest_endpoint_with_gst(), test_range_query_json_and_csv() (+2 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (35): dependencies, clsx, lucide-react, react, react-dom, tailwind-merge, devDependencies, autoprefixer (+27 more)

### Community 4 - "test_scheduler.py"
Cohesion: 0.07
Nodes (15): now_ist(), now_utc(), parse_hhmm(), parse_iso_utc(), to_utc_iso(), HolidayCalendar, TokenBucketRateLimiter, calculate_next_business_window() (+7 more)

### Community 5 - "AGENTS.md — SilverSurf Project Guide"
Cohesion: 0.25
Nodes (8): 1. System Overview, 2. Directory Layout, 3. Developer & Verification Workflows, 4. Architectural Guardrails for Agents, AGENTS.md — SilverSurf Project Guide, Backend Workflows, Frontend Workflows, Full-Stack Docker Deployment

### Community 6 - "Session"
Cohesion: 0.22
Nodes (11): Metal, RateStatus, Session, ValidationPipeline, ValidationResult, test_ibja_html_source_parses_sample_page(), test_v1_price_bounds_rejection(), test_v2_dod_spike_quarantine() (+3 more)

### Community 7 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 8 - "App.tsx"
Cohesion: 0.14
Nodes (12): 4.1 `useRateStream` (Real-Time SSE Management), 4.2 `useLatestRate`, 4.3 `useRateHistory`, 4. Frontend State & Custom Hooks, App(), Attribution(), Header(), useLatestRate() (+4 more)

### Community 9 - "LiveRateCard.tsx"
Cohesion: 0.36
Nodes (8): LiveRateCard(), Toggle(), RateUnit, calculateWithGST(), convertRateUnit(), getUnitDisplayLabel(), GST_RATE, formatISTTime()

### Community 10 - "Header.tsx"
Cohesion: 0.24
Nodes (7): HeaderProps, useHealthStatus(), UseHealthStatusOptions, HealthStatus, HealthStatusType, SchedulerMode, SSEConnectionState

### Community 11 - "HistoryTable.tsx"
Cohesion: 0.19
Nodes (16): HistoryTable(), HistoryTableProps, SortField, SortOrder, DatePoint, TrendChart(), TrendChartProps, Badge() (+8 more)

### Community 12 - "PRD: SilverSurf (IBJA Silver Rate Scraper & Live Feed)"
Cohesion: 0.14
Nodes (14): 10. Testing & QA, 12. Success Metrics, 13. Milestones, 14. Discovery Spike Checklist (Phase 0), 15. Open Questions, 16. Out of Scope for v1 / Future, 2. Problem & Opportunity, 3. Goals / Non-Goals (+6 more)

### Community 13 - "silver.ts"
Cohesion: 0.15
Nodes (10): LiveRateCardProps, UseLatestRateOptions, UseRateStreamOptions, HistoryResponse, MetalType, PurityType, RateStatus, SilverRate (+2 more)

### Community 14 - "react"
Cohesion: 0.29
Nodes (5): BadgeProps, BadgeVariant, variantStyles, ToggleProps, react

### Community 15 - "architecture.md"
Cohesion: 0.18
Nodes (8): 1. OpenAPI & TypeScript Data Contract, 1. Tech Stack & Engineering Choices, 2. Design System & Tokens (Claude Warm Editorial), 2. Docker & Single-Node Deployment Topology, 3. Component Hierarchy & Layout, 3. Verification & Quality Gates, Part II: Frontend Architecture, Part III: Integration Contracts, Deployment & Verification

### Community 16 - "Part I: Backend Architecture"
Cohesion: 0.22
Nodes (9): 1. Core Technologies & Dependencies, 2. Ingestion Pipeline & The `RateSource` Abstraction, 3.1 State Machine Modes, 3. Adaptive Scheduling Engine, 4. Validation Rules (V1–V5), 5.1 Revisions & Upsert Logic, 5. Storage Schema (SQLite WAL Mode), 6. Staleness Evaluation Engine (+1 more)

### Community 17 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 18 - "RateSource"
Cohesion: 0.25
Nodes (3): RateSource, 11. Legal, Compliance & Risk (gate for launch), 1. Summary

### Community 19 - "RawScrapeResult"
Cohesion: 0.18
Nodes (4): RawScrapeResult, IbjaPdfBackfillSource, FakeSource, test_ibja_pdf_parser_mock()

### Community 20 - "6. Scope: Functional Requirements"
Cohesion: 0.29
Nodes (7): 6.1 Acquisition, 6.2 Scheduling ("live" behaviour), 6.3 Validation (reject-and-alert, never silently store), 6.4 Storage, 6.5 Timestamps, 6.6 Derived values, 6. Scope: Functional Requirements

### Community 22 - "SSEEventBus"
Cohesion: 0.17
Nodes (3): SSEEventBus, SubscriberLimitReached, test_sse_bus_fanout()

### Community 37 - "useRateHistory.ts"
Cohesion: 0.31
Nodes (4): useRateHistory(), HistoryQueryParams, formatISTDateISO(), getISTDateRange()

### Community 38 - "silver.py"
Cohesion: 0.19
Nodes (7): get_silver_by_date(), get_silver_range(), list_quarantined_silver(), silver_rate_stream(), _to_rate_summary(), PaginatedRatesResponse, RateItemSummary

### Community 39 - "schemas.py"
Cohesion: 0.18
Nodes (6): get_health(), SchedulerMode, DateRatesResponse, HealthStatus, SilverRate, SSERateEvent

### Community 40 - "RateRepository"
Cohesion: 0.14
Nodes (6): get_metrics(), get_latest_silver(), ScrapeSummary, RateRepository, test_scheduler_poll_once_end_to_end(), scheduler()

### Community 41 - "RateRecord"
Cohesion: 0.16
Nodes (3): RateRecord, QuarantineManager, test_quarantine_management()

### Community 43 - "StalenessBanner.tsx"
Cohesion: 0.47
Nodes (4): StalenessBanner(), StalenessBannerProps, StaleReason, formatISTDateTime()

### Community 44 - "test_parser.py"
Cohesion: 0.16
Nodes (6): ParserIntegrityError, QuarantineError, RateNotFoundError, SilverSurfError, ValidationError, test_ibja_html_source_malformed_raises_error()

### Community 45 - "7. REST & SSE API Specification"
Cohesion: 0.33
Nodes (6): 7.1 `GET /v1/silver/latest`, 7.2 `GET /v1/silver/{date}`, 7.3 `GET /v1/silver`, 7.4 `GET /v1/silver/stream`, 7.5 `GET /v1/health`, 7. REST & SSE API Specification

### Community 46 - "SilverSurf Architecture Document"
Cohesion: 0.40
Nodes (5): Core Architecture Principles, Executive Summary & System Overview, SilverSurf Architecture Document, System Flow Diagram, System Topology & Monorepo Structure

## Knowledge Gaps
- **117 isolated node(s):** `silversurf-backend`, `name`, `private`, `version`, `type` (+112 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 254 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Part I: Backend Architecture` connect `Part I: Backend Architecture` to `7. REST & SSE API Specification`, `architecture.md`?**
  _High betweenness centrality (0.351) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `RawScrapeResult` (e.g. with `Metal` and `Session`) actually correct?**
  _`RawScrapeResult` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `silversurf-backend`, `name`, `private` to the rest of the system?**
  _117 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `IbjaHtmlSource` be split into smaller, more focused modules?**
  _Cohesion score 0.09879032258064516 - nodes in this community are weakly interconnected._
- **Why does `Part II: Frontend Architecture` connect `architecture.md` to `App.tsx`?**
  _High betweenness centrality (0.338) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `RateRepository` (e.g. with `get_health()` and `get_metrics()`) actually correct?**
  _`RateRepository` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `AdaptiveScheduler` be split into smaller, more focused modules?**
  _Cohesion score 0.06386066763425254 - nodes in this community are weakly interconnected._