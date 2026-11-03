import gzip
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import pytest

from app.storage.database import get_connection, init_db
from app.storage.snapshots import SnapshotManager


@pytest.fixture
async def temp_storage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test.db")
        snaps_dir = str(Path(tmp_dir) / "snapshots")
        await init_db(db_path)
        yield db_path, snaps_dir


@pytest.mark.asyncio
async def test_snapshot_save_read_and_prune(temp_storage):
    db_path, snaps_dir = temp_storage
    manager = SnapshotManager(snaps_dir)

    raw_html = b"<html><body><h1>Test Snapshot</h1></body></html>"
    sha = hashlib.sha256(raw_html).hexdigest()

    async with get_connection(db_path) as conn:
        # 1. Save snapshot
        snap_id = await manager.save_snapshot(conn, raw_html, http_status=200)
        assert snap_id is not None

        # Verify file exists on disk and is gzipped
        file_path = Path(snaps_dir) / f"{snap_id}.html.gz"
        assert file_path.exists()
        assert gzip.decompress(file_path.read_bytes()) == raw_html

        # Verify DB entry
        async with conn.execute("SELECT * FROM snapshots WHERE id = ?", (snap_id,)) as cursor:
            row = await cursor.fetchone()
            assert row["sha256"] == sha
            assert row["http_status"] == 200

        # 2. Read snapshot
        read_bytes = await manager.read_snapshot(conn, snap_id)
        assert read_bytes == raw_html

        # 3. Test pruning
        # Update fetched_at to 100 days ago
        old_time = (datetime.now(timezone.utc) - timedelta(days=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        await conn.execute("UPDATE snapshots SET fetched_at = ? WHERE id = ?", (old_time, snap_id))
        await conn.commit()

        pruned_snaps, _ = await manager.prune_expired(conn, snapshot_retention_days=90)
        assert pruned_snaps == 1
        assert not file_path.exists()

        # Check DB row is gone
        async with conn.execute("SELECT * FROM snapshots WHERE id = ?", (snap_id,)) as cursor:
            row = await cursor.fetchone()
            assert row is None
