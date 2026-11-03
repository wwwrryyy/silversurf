PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- Snapshots table: audit trail of raw HTML/PDF
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    http_status INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    file_path TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_sha ON snapshots(sha256);

-- Rates table: benchmark rates with revision handling
CREATE TABLE IF NOT EXISTS rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rate_date TEXT NOT NULL,
    session TEXT NOT NULL CHECK(session IN ('AM', 'PM')),
    metal TEXT NOT NULL,
    purity TEXT NOT NULL,
    price_inr REAL NOT NULL,
    unit TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'valid' CHECK(status IN ('valid', 'quarantined', 'superseded')),
    revision INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    snapshot_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE SET NULL,
    UNIQUE(rate_date, session, metal, purity, revision)
);

CREATE INDEX IF NOT EXISTS idx_rates_lookup ON rates(metal, purity, rate_date DESC, session DESC);
CREATE INDEX IF NOT EXISTS idx_rates_status ON rates(status);

-- Scrape runs table: operational telemetry
CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'no_change', 'error', 'quarantined')),
    records_new INTEGER NOT NULL DEFAULT 0,
    records_changed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
