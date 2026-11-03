import asyncio
import gzip
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import aiosqlite

from app.config import settings
from app.core.time_utils import now_utc, to_utc_iso


class SnapshotManager:
    def __init__(self, snapshots_dir: str | Path | None = None):
        self.snapshots_dir = Path(snapshots_dir or settings.snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    async def save_snapshot(
        self,
        conn: aiosqlite.Connection,
        raw_bytes: bytes,
        http_status: int = 200,
        fetched_at: datetime | None = None,
    ) -> str:
        """
        Compress and store raw HTML/PDF payload, returning the snapshot UUID.
        """
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        # SHA-256 deduplication: reuse an identical existing snapshot
        async with conn.execute(
            "SELECT id FROM snapshots WHERE sha256 = ? LIMIT 1", (sha256_hash,)
        ) as cursor:
            existing = await cursor.fetchone()
        if existing:
            return existing["id"]

        snapshot_id = str(uuid.uuid4())
        fetched_time = fetched_at or now_utc()
        fetched_iso = to_utc_iso(fetched_time) or ""

        file_path = self.snapshots_dir / f"{snapshot_id}.html.gz"
        await asyncio.to_thread(lambda: file_path.write_bytes(gzip.compress(raw_bytes)))

        await conn.execute(
            """
            INSERT INTO snapshots (id, fetched_at, http_status, sha256, file_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (snapshot_id, fetched_iso, http_status, sha256_hash, str(file_path)),
        )
        await conn.commit()
        return snapshot_id

    async def read_snapshot(self, conn: aiosqlite.Connection, snapshot_id: str) -> bytes | None:
        """Read and decompress raw snapshot bytes."""
        async with conn.execute(
            "SELECT file_path FROM snapshots WHERE id = ?", (snapshot_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            path = Path(row["file_path"])
            if not path.exists():
                return None
            return await asyncio.to_thread(lambda: gzip.decompress(path.read_bytes()))

    async def prune_expired(
        self,
        conn: aiosqlite.Connection,
        snapshot_retention_days: int | None = None,
        run_retention_days: int | None = None,
    ) -> tuple[int, int]:
        """
        Prune snapshots older than retention days and scrape_runs older than run_retention_days.
        Returns: (pruned_snapshots_count, pruned_runs_count)
        """
        snap_days = snapshot_retention_days or settings.snapshot_retention_days
        run_days = run_retention_days or settings.scrape_run_retention_days

        cutoff_snaps = to_utc_iso(now_utc() - timedelta(days=snap_days)) or ""
        cutoff_runs = to_utc_iso(now_utc() - timedelta(days=run_days)) or ""

        # Find expired snapshots
        async with conn.execute(
            "SELECT id, file_path FROM snapshots WHERE fetched_at < ?", (cutoff_snaps,)
        ) as cursor:
            expired_snaps = await cursor.fetchall()

        pruned_snaps = 0
        for snap in expired_snaps:
            snap_path = Path(snap["file_path"])
            try:
                if snap_path.exists():
                    snap_path.unlink()
            except OSError:
                pass
            await conn.execute("DELETE FROM snapshots WHERE id = ?", (snap["id"],))
            pruned_snaps += 1

        # Prune expired scrape_runs
        cursor_runs = await conn.execute(
            "DELETE FROM scrape_runs WHERE started_at < ?", (cutoff_runs,)
        )
        pruned_runs = cursor_runs.rowcount

        await conn.commit()
        return pruned_snaps, pruned_runs
