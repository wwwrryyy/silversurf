from dataclasses import dataclass
import aiosqlite

from app.core.time_utils import now_utc, to_utc_iso


@dataclass(frozen=True)
class RateRecord:
    id: int
    rate_date: str
    session: str
    metal: str
    purity: str
    price_inr: float
    unit: str
    status: str
    revision: int
    first_seen_at: str
    source_url: str
    snapshot_id: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "RateRecord":
        return cls(
            id=row["id"],
            rate_date=row["rate_date"],
            session=row["session"],
            metal=row["metal"],
            purity=row["purity"],
            price_inr=float(row["price_inr"]),
            unit=row["unit"],
            status=row["status"],
            revision=int(row["revision"]),
            first_seen_at=row["first_seen_at"],
            source_url=row["source_url"],
            snapshot_id=row["snapshot_id"],
            created_at=row["created_at"],
        )


class RateRepository:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def save_rate(
        self,
        rate_date: str,
        session: str,
        metal: str,
        purity: str,
        price_inr: float,
        unit: str,
        status: str,
        first_seen_at: str,
        source_url: str,
        snapshot_id: str | None = None,
    ) -> tuple[RateRecord, bool, bool]:
        """
        Idempotent save with revision detection.
        Returns: (record, is_new, is_revised)
        """
        now_str = to_utc_iso(now_utc()) or ""

        # Check existing records for this (date, session, metal, purity)
        async with self.conn.execute(
            """
            SELECT * FROM rates
            WHERE rate_date = ? AND session = ? AND metal = ? AND purity = ?
            ORDER BY revision DESC LIMIT 1
            """,
            (rate_date, session, metal, purity),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # First publication of this rate
            cursor = await self.conn.execute(
                """
                INSERT INTO rates (
                    rate_date, session, metal, purity, price_inr, unit,
                    status, revision, first_seen_at, source_url, snapshot_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                (
                    rate_date,
                    session,
                    metal,
                    purity,
                    price_inr,
                    unit,
                    status,
                    first_seen_at,
                    source_url,
                    snapshot_id,
                    now_str,
                ),
            )
            inserted_id = cursor.lastrowid
            await self.conn.commit()
            record = await self.get_by_id(inserted_id)
            return record, True, False

        existing = RateRecord.from_row(row)

        # Idempotent match: same price and status
        if existing.price_inr == price_inr and existing.status == status:
            return existing, False, False

        # Price revision or status update
        next_revision = existing.revision + 1
        await self.conn.execute(
            "UPDATE rates SET status = 'superseded' WHERE id = ?", (existing.id,)
        )
        cursor = await self.conn.execute(
            """
            INSERT INTO rates (
                rate_date, session, metal, purity, price_inr, unit,
                status, revision, first_seen_at, source_url, snapshot_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rate_date,
                session,
                metal,
                purity,
                price_inr,
                unit,
                status,
                next_revision,
                first_seen_at,
                source_url,
                snapshot_id,
                now_str,
            ),
        )
        inserted_id = cursor.lastrowid
        await self.conn.commit()
        record = await self.get_by_id(inserted_id)
        return record, False, True

    async def get_by_id(self, record_id: int) -> RateRecord:
        async with self.conn.execute("SELECT * FROM rates WHERE id = ?", (record_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Rate with id {record_id} not found")
            return RateRecord.from_row(row)

    async def get_latest_rate(
        self, metal: str = "silver", purity: str = "999"
    ) -> RateRecord | None:
        """Fetch the most recent valid published benchmark rate."""
        async with self.conn.execute(
            """
            SELECT * FROM rates
            WHERE metal = ? AND purity = ? AND status = 'valid'
            ORDER BY rate_date DESC, session DESC, revision DESC
            LIMIT 1
            """,
            (metal, purity),
        ) as cursor:
            row = await cursor.fetchone()
            return RateRecord.from_row(row) if row else None

    async def get_rates_by_date(
        self, rate_date: str, metal: str = "silver", purity: str = "999"
    ) -> list[RateRecord]:
        """Fetch valid rates for a specific calendar date (AM and PM)."""
        async with self.conn.execute(
            """
            SELECT * FROM rates
            WHERE rate_date = ? AND metal = ? AND purity = ? AND status = 'valid'
            ORDER BY session ASC, revision DESC
            """,
            (rate_date, metal, purity),
        ) as cursor:
            rows = await cursor.fetchall()
            seen_sessions: set[str] = set()
            results: list[RateRecord] = []
            for r in rows:
                rec = RateRecord.from_row(r)
                if rec.session not in seen_sessions:
                    seen_sessions.add(rec.session)
                    results.append(rec)
            return results

    async def get_rates_range(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        session: str | None = None,
        metal: str = "silver",
        purity: str = "999",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RateRecord], int]:
        """Paginated historical query."""
        clauses = ["metal = ?", "purity = ?", "status = 'valid'"]
        params: list = [metal, purity]

        if from_date:
            clauses.append("rate_date >= ?")
            params.append(from_date)
        if to_date:
            clauses.append("rate_date <= ?")
            params.append(to_date)
        if session:
            clauses.append("session = ?")
            params.append(session)

        where_clause = " AND ".join(clauses)

        # Count total
        count_query = f"SELECT COUNT(*) FROM rates WHERE {where_clause}"
        async with self.conn.execute(count_query, params) as cursor:
            total_count = (await cursor.fetchone())[0]

        # Select items
        items_query = f"""
            SELECT * FROM rates
            WHERE {where_clause}
            ORDER BY rate_date DESC, session DESC, revision DESC
            LIMIT ? OFFSET ?
        """
        async with self.conn.execute(items_query, params + [limit, offset]) as cursor:
            rows = await cursor.fetchall()
            items = [RateRecord.from_row(r) for r in rows]

        return items, total_count

    async def get_previous_valid_rate(
        self, before_date: str, metal: str = "silver", purity: str = "999"
    ) -> RateRecord | None:
        """Fetch the latest valid rate prior to the specified date (for DoD calculation)."""
        async with self.conn.execute(
            """
            SELECT * FROM rates
            WHERE metal = ? AND purity = ? AND status = 'valid' AND rate_date < ?
            ORDER BY rate_date DESC, session DESC, revision DESC
            LIMIT 1
            """,
            (metal, purity, before_date),
        ) as cursor:
            row = await cursor.fetchone()
            return RateRecord.from_row(row) if row else None

    async def record_scrape_run(
        self,
        started_at: str,
        finished_at: str,
        outcome: str,
        records_new: int,
        records_changed: int,
        error_message: str | None = None,
    ) -> int:
        cursor = await self.conn.execute(
            """
            INSERT INTO scrape_runs (
                started_at, finished_at, outcome, records_new, records_changed, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (started_at, finished_at, outcome, records_new, records_changed, error_message),
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_last_successful_scrape(self) -> str | None:
        async with self.conn.execute(
            """
            SELECT finished_at FROM scrape_runs
            WHERE outcome IN ('success', 'no_change')
            ORDER BY id DESC LIMIT 1
            """
        ) as cursor:
            row = await cursor.fetchone()
            return row["finished_at"] if row else None

    async def get_quarantined_count(self) -> int:
        async with self.conn.execute(
            "SELECT COUNT(*) FROM rates WHERE status = 'quarantined'"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
