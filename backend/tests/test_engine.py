import asyncio
from datetime import date
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from app.domain.metal import Metal, RateStatus, Session
from app.events.sse_bus import SSEEventBus
from app.scheduler.engine import AdaptiveScheduler
from app.sources.base import RawScrapeResult
from app.sources.ibja_pdf import IbjaPdfBackfillSource
from app.storage.database import get_connection, init_db
from app.storage.repository import RateRepository
from app.validation.quarantine import QuarantineManager


class FakeSource:
    def __init__(self, records: list[RawScrapeResult]):
        self.records = records

    async def fetch_latest(self) -> list[RawScrapeResult]:
        return self.records

    async def fetch_historical_pdf(self, url: str) -> list[RawScrapeResult]:
        return self.records


@pytest.fixture
async def temp_env():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test.db")
        snaps_dir = str(Path(tmp_dir) / "snapshots")
        await init_db(db_path)
        yield db_path, snaps_dir


@pytest.mark.asyncio
async def test_scheduler_poll_once_end_to_end(temp_env):
    db_path, snaps_dir = temp_env

    mock_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=98500.0,
        unit="per_kg",
        raw_html_bytes=b"<html>mock</html>",
        http_status=200,
        source_url="https://ibjarates.com",
    )
    fake_source = FakeSource([mock_record])

    scheduler = AdaptiveScheduler(
        db_path=db_path,
        snapshots_dir=snaps_dir,
        html_source=fake_source,
    )

    # First poll: new record
    summary = await scheduler.poll_once()
    assert summary.outcome == "success"
    assert summary.records_new == 1
    assert summary.records_changed == 0

    # Verify saved in DB
    async with get_connection(db_path) as conn:
        repo = RateRepository(conn)
        latest = await repo.get_latest_rate("silver", "999")
        assert latest is not None
        assert latest.price_inr == 98500.0
        assert latest.snapshot_id is not None

    # Second poll with same record: idempotent no_change
    summary2 = await scheduler.poll_once()
    assert summary2.outcome == "no_change"
    assert summary2.records_new == 0
    assert summary2.records_changed == 0


@pytest.mark.asyncio
async def test_quarantine_management(temp_env):
    db_path, _ = temp_env

    async with get_connection(db_path) as conn:
        repo = RateRepository(conn)
        rec, _, _ = await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=150000.0,
            unit="per_kg",
            status="quarantined",
            first_seen_at="2026-11-02T06:36:12Z",
            source_url="https://ibjarates.com",
        )

        q_manager = QuarantineManager(conn)
        q_list = await q_manager.list_quarantined()
        assert len(q_list) == 1
        assert q_list[0].id == rec.id

        # Approve record
        approved = await q_manager.approve_record(rec.id)
        assert approved is True

        # Now valid
        updated = await repo.get_by_id(rec.id)
        assert updated.status == RateStatus.VALID.value
        assert len(await q_manager.list_quarantined()) == 0


@pytest.mark.asyncio
async def test_sse_bus_fanout():
    bus = SSEEventBus()

    async def consumer():
        events = []
        gen = bus.subscribe(initial_comment=False)
        try:
            async for ev in gen:
                events.append(ev)
                if len(events) >= 2:
                    break
        finally:
            await gen.aclose()
        return events

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.01)

    # Publish events
    await bus.publish("rate.published", {"price_inr": 98500})
    await bus.publish("rate.revised", {"price_inr": 98600})

    received = await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 2
    assert "event: rate.published" in received[0]
    assert "98500" in received[0]
    assert "event: rate.revised" in received[1]
    assert "98600" in received[1]


def test_ibja_pdf_parser_mock():
    source = IbjaPdfBackfillSource()

    mock_page = MagicMock()
    mock_page.extract_tables.return_value = [
        [
            ["Date", "Session", "Silver 999", "Gold 999"],
            ["02/11/2026", "AM", "98,500", "78,500"],
            ["02/11/2026", "PM", "98,800", "78,600"],
        ]
    ]

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        results = source.parse_pdf(b"%PDF-mock", source_url="test.pdf")
        assert len(results) == 2
        assert results[0].rate_date == date(2026, 11, 2)
        assert results[0].session == Session.AM
        assert results[0].price_inr == 98500.0
        assert results[1].session == Session.PM
        assert results[1].price_inr == 98800.0
