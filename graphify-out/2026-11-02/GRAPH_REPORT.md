# Graph Report - silversurf  (2026-11-02)

## Corpus Check
- 72 files · ~24,151 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .conf 1, .css 1)

## Summary
- 562 nodes · 1251 edges · 36 communities (22 shown, 14 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 143 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- IbjaHtmlSource
- time_utils.py
- RateRepository
- package.json
- AdaptiveScheduler
- AGENTS.md — SilverSurf Project Guide
- engine.py
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
- Part III: Integration Contracts, Deployment & Verification
- 6. Scope: Functional Requirements
- Notifier
- useLatestRate.ts
- silversurf-backend

## God Nodes (most connected - your core abstractions)
1. `RawScrapeResult` - 35 edges
2. `RateRepository` - 32 edges
3. `Session` - 30 edges
4. `AdaptiveScheduler` - 30 edges
5. `IbjaHtmlSource` - 29 edges
6. `get_connection()` - 26 edges
7. `Metal` - 25 edges
8. `RateRecord` - 21 edges
9. `RateStatus` - 19 edges
10. `IbjaPdfBackfillSource` - 19 edges

## Surprising Connections (you probably didn't know these)
- `4. Validation Rules (V1–V5)` --references--> `ValidationPipeline`  [INFERRED]
  architecture.md → backend/app/validation/rules.py
- `2. Ingestion Pipeline & The `RateSource` Abstraction` --references--> `RateSource`  [INFERRED]
  architecture.md → backend/app/sources/base.py
- `Core Architecture Principles` --references--> `RateSource`  [INFERRED]
  architecture.md → backend/app/sources/base.py
- `11. Legal, Compliance & Risk (gate for launch)` --references--> `RateSource`  [INFERRED]
  PRD.md → backend/app/sources/base.py
- `1. Summary` --references--> `RateSource`  [INFERRED]
  PRD.md → backend/app/sources/base.py

## Import Cycles
- None detected.

## Communities (36 total, 14 thin omitted)

### Community 0 - "IbjaHtmlSource"
Cohesion: 0.06
Nodes (11): 2.1 Extraction Strategy (`IbjaHtmlSource`), 2. Ingestion Pipeline & The `RateSource` Abstraction, ParserIntegrityError, parse_dd_mm_yyyy_ist(), IbjaHtmlSource, IbjaPdfBackfillSource, PlaywrightFallbackSource, test_ibja_pdf_parser_mock() (+3 more)

### Community 1 - "time_utils.py"
Cohesion: 0.06
Nodes (14): now_ist(), now_utc(), parse_iso_utc(), to_utc_iso(), lifespan(), root(), calculate_next_business_window(), compute_staleness() (+6 more)

### Community 2 - "RateRepository"
Cohesion: 0.05
Nodes (22): get_health(), get_metrics(), get_latest_silver(), get_silver_by_date(), silver_rate_stream(), _to_rate_summary(), SSEEventBus, get_connection() (+14 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (35): dependencies, clsx, lucide-react, react, react-dom, tailwind-merge, devDependencies, autoprefixer (+27 more)

### Community 4 - "AdaptiveScheduler"
Cohesion: 0.09
Nodes (10): SchedulerMode, HolidayCalendar, AdaptiveScheduler, TokenBucketRateLimiter, MockCalendar, scheduler(), test_calendar(), test_scheduler_ist_mode_transitions() (+2 more)

### Community 5 - "AGENTS.md — SilverSurf Project Guide"
Cohesion: 0.25
Nodes (8): 1. System Overview, 2. Directory Layout, 3. Developer & Verification Workflows, 4. Architectural Guardrails for Agents, AGENTS.md — SilverSurf Project Guide, Backend Workflows, Frontend Workflows, Full-Stack Docker Deployment

### Community 6 - "engine.py"
Cohesion: 0.07
Nodes (27): get_silver_range(), _to_silver_rate_dto(), Settings, QuarantineError, RateNotFoundError, SilverSurfError, SourceFetchError, ValidationError (+19 more)

### Community 7 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 8 - "App.tsx"
Cohesion: 0.16
Nodes (13): 4.1 `useRateStream` (Real-Time SSE Management), 4.2 `useLatestRate`, 4.3 `useRateHistory`, 4. Frontend State & Custom Hooks, App(), DEMO_FALLBACK_HISTORY, DEMO_FALLBACK_RATE, Attribution() (+5 more)

### Community 9 - "LiveRateCard.tsx"
Cohesion: 0.23
Nodes (14): HistoryTable(), LiveRateCard(), TrendChart(), Badge(), Button(), Toggle(), RateUnit, calculateWithGST() (+6 more)

### Community 10 - "Header.tsx"
Cohesion: 0.18
Nodes (9): HeaderProps, useHealthStatus(), UseHealthStatusOptions, UseRateStreamOptions, HealthStatus, HealthStatusType, SchedulerMode, SSEConnectionState (+1 more)

### Community 11 - "HistoryTable.tsx"
Cohesion: 0.16
Nodes (11): HistoryTableProps, SortField, SortOrder, DatePoint, TrendChartProps, ButtonProps, ButtonSize, ButtonVariant (+3 more)

### Community 12 - "PRD: SilverSurf (IBJA Silver Rate Scraper & Live Feed)"
Cohesion: 0.14
Nodes (14): 10. Testing & QA, 12. Success Metrics, 13. Milestones, 14. Discovery Spike Checklist (Phase 0), 15. Open Questions, 16. Out of Scope for v1 / Future, 2. Problem & Opportunity, 3. Goals / Non-Goals (+6 more)

### Community 13 - "silver.ts"
Cohesion: 0.20
Nodes (9): StalenessBanner(), StalenessBannerProps, HistoryResponse, MetalType, PurityType, RateStatus, SSERateEventName, StaleReason (+1 more)

### Community 14 - "react"
Cohesion: 0.18
Nodes (7): BadgeProps, BadgeVariant, variantStyles, ToggleProps, rootElement, react, react-dom

### Community 15 - "architecture.md"
Cohesion: 0.20
Nodes (7): 1. Tech Stack & Engineering Choices, 2. Design System & Tokens (Dark OLED Terminal), 3. Component Hierarchy & Layout, Part II: Frontend Architecture, SilverSurf Architecture Document, System Flow Diagram, System Topology & Monorepo Structure

### Community 16 - "Part I: Backend Architecture"
Cohesion: 0.14
Nodes (14): 1. Core Technologies & Dependencies, 3.1 State Machine Modes, 3. Adaptive Scheduling Engine, 4. Validation Rules (V1–V5), 5.1 Revisions & Upsert Logic, 5. Storage Schema (SQLite WAL Mode), 6. Staleness Evaluation Engine, 7.1 `GET /v1/silver/latest` (+6 more)

### Community 17 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 18 - "RateSource"
Cohesion: 0.20
Nodes (5): Core Architecture Principles, Executive Summary & System Overview, RateSource, 11. Legal, Compliance & Risk (gate for launch), 1. Summary

### Community 19 - "Part III: Integration Contracts, Deployment & Verification"
Cohesion: 0.50
Nodes (4): 1. OpenAPI & TypeScript Data Contract, 2. Docker & Single-Node Deployment Topology, 3. Verification & Quality Gates, Part III: Integration Contracts, Deployment & Verification

### Community 20 - "6. Scope: Functional Requirements"
Cohesion: 0.29
Nodes (7): 6.1 Acquisition, 6.2 Scheduling ("live" behaviour), 6.3 Validation (reject-and-alert, never silently store), 6.4 Storage, 6.5 Timestamps, 6.6 Derived values, 6. Scope: Functional Requirements

### Community 22 - "useLatestRate.ts"
Cohesion: 0.40
Nodes (3): LiveRateCardProps, UseLatestRateOptions, SilverRate

## Knowledge Gaps
- **119 isolated node(s):** `silversurf-backend`, `name`, `private`, `version`, `type` (+114 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 243 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Part I: Backend Architecture` connect `Part I: Backend Architecture` to `IbjaHtmlSource`, `architecture.md`?**
  _High betweenness centrality (0.356) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `RawScrapeResult` (e.g. with `Metal` and `Session`) actually correct?**
  _`RawScrapeResult` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `silversurf-backend`, `name`, `private` to the rest of the system?**
  _119 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `IbjaHtmlSource` be split into smaller, more focused modules?**
  _Cohesion score 0.0632996632996633 - nodes in this community are weakly interconnected._
- **Why does `Part II: Frontend Architecture` connect `architecture.md` to `App.tsx`?**
  _High betweenness centrality (0.346) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `RateRepository` (e.g. with `get_health()` and `get_metrics()`) actually correct?**
  _`RateRepository` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `time_utils.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06271186440677966 - nodes in this community are weakly interconnected._