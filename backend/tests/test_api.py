import asyncio
from pathlib import Path
import tempfile
import httpx
import pytest
from httpx import ASGITransport

from app.config import settings
from app.domain.metal import RateStatus
from app.events.sse_bus import sse_bus
from app.main import app
from app.storage.database import get_connection, init_db
from app.storage.repository import RateRepository


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Create a clean isolated SQLite database for each test."""
    temp_dir = tempfile.TemporaryDirectory()
    test_db_path = str(Path(temp_dir.name) / "test_silversurf.db")
    test_snaps_path = str(Path(temp_dir.name) / "snapshots")

    monkeypatch.setattr(settings, "database_path", test_db_path)
    monkeypatch.setattr(settings, "snapshots_dir", test_snaps_path)
    monkeypatch.setattr(settings, "environment", "testing")

    await init_db(test_db_path)
    yield
    temp_dir.cleanup()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_latest_endpoint_empty_and_populated(client):
    # 1. 404 when no rates
    res = await client.get("/v1/silver/latest")
    assert res.status_code == 404

    # 2. Populate a rate
    async with get_connection() as conn:
        repo = RateRepository(conn)
        await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=98500.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T06:36:12Z",
            source_url="https://ibjarates.com",
        )

    res = await client.get("/v1/silver/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["metal"] == "silver"
    assert data["purity"] == "999"
    assert data["price_inr_per_kg"] == 98500.0
    assert data["price_inr_per_10g"] == 985.0
    assert data["price_inr_per_gram"] == 98.5
    assert data["excludes_gst"] is True
    assert data["derived"] is False
    assert data["revision"] == 1


@pytest.mark.asyncio
async def test_latest_endpoint_with_gst(client):
    async with get_connection() as conn:
        repo = RateRepository(conn)
        await repo.save_rate(
            rate_date="2026-11-02",
            session="PM",
            metal="silver",
            purity="999",
            price_inr=100000.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T11:36:12Z",
            source_url="https://ibjarates.com",
        )

    res = await client.get("/v1/silver/latest?include_gst=true")
    assert res.status_code == 200
    data = res.json()
    # 100,000 * 1.03 = 103,000
    assert data["price_inr_per_kg"] == 103000.0
    assert data["price_inr_per_10g"] == 1030.0
    assert data["price_inr_per_gram"] == 103.0
    assert data["excludes_gst"] is False
    assert data["derived"] is True


@pytest.mark.asyncio
async def test_stream_endpoint_route_resolution():
    """Verify that /v1/silver/stream is registered and precedes /{rate_date} in path resolution."""
    paths = list(app.openapi()["paths"].keys())
    assert "/v1/silver/stream" in paths
    assert "/v1/silver/{rate_date}" in paths
    stream_idx = paths.index("/v1/silver/stream")
    date_idx = paths.index("/v1/silver/{rate_date}")
    assert stream_idx < date_idx, "Route /stream must precede /{rate_date} to prevent shadowing"


@pytest.mark.asyncio
async def test_date_endpoint(client):
    async with get_connection() as conn:
        repo = RateRepository(conn)
        await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=98500.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T06:36:12Z",
            source_url="https://ibjarates.com",
        )
        await repo.save_rate(
            rate_date="2026-11-02",
            session="PM",
            metal="silver",
            purity="999",
            price_inr=98800.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T11:36:12Z",
            source_url="https://ibjarates.com",
        )

    res = await client.get("/v1/silver/2026-11-02")
    assert res.status_code == 200
    data = res.json()
    assert data["rate_date"] == "2026-11-02"
    assert data["am"]["price_inr_per_kg"] == 98500.0
    assert data["pm"]["price_inr_per_kg"] == 98800.0

    # 404 for unknown date
    res_404 = await client.get("/v1/silver/2026-10-01")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_range_query_json_and_csv(client):
    async with get_connection() as conn:
        repo = RateRepository(conn)
        for i in range(5):
            d = f"2026-11-0{i+1}"
            await repo.save_rate(
                rate_date=d,
                session="AM",
                metal="silver",
                purity="999",
                price_inr=98000.0 + (i * 100),
                unit="per_kg",
                status="valid",
                first_seen_at="2026-11-01T06:36:12Z",
                source_url="https://ibjarates.com",
            )

    # JSON range
    res_json = await client.get("/v1/silver?limit=3&offset=0")
    assert res_json.status_code == 200
    data = res_json.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3

    # CSV export
    res_csv = await client.get("/v1/silver?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    csv_lines = res_csv.text.strip().split("\r\n") if "\r\n" in res_csv.text else res_csv.text.strip().split("\n")
    assert len(csv_lines) == 6  # header + 5 items
    assert "rate_date,session,metal" in csv_lines[0]


@pytest.mark.asyncio
async def test_health_and_metrics_endpoints(client):
    res_health = await client.get("/v1/health")
    assert res_health.status_code == 200
    health = res_health.json()
    assert health["status"] in ("healthy", "degraded", "unhealthy")
    assert "scheduler_mode" in health
    assert "parser_healthy" in health

    res_metrics = await client.get("/v1/metrics")
    assert res_metrics.status_code == 200
    assert "silversurf_scrape_total" in res_metrics.text
    assert "silversurf_parser_healthy" in res_metrics.text


@pytest.mark.asyncio
async def test_revision_and_idempotency():
    async with get_connection() as conn:
        repo = RateRepository(conn)

        # 1. First insert
        r1, is_new, is_revised = await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=98500.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T06:36:12Z",
            source_url="https://ibjarates.com",
        )
        assert is_new is True
        assert is_revised is False
        assert r1.revision == 1

        # 2. Idempotent re-run with same price
        r2, is_new, is_revised = await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=98500.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T06:36:12Z",
            source_url="https://ibjarates.com",
        )
        assert is_new is False
        assert is_revised is False
        assert r2.id == r1.id
        assert r2.revision == 1

        # 3. Revision: price corrected to 98,600
        r3, is_new, is_revised = await repo.save_rate(
            rate_date="2026-11-02",
            session="AM",
            metal="silver",
            purity="999",
            price_inr=98600.0,
            unit="per_kg",
            status="valid",
            first_seen_at="2026-11-02T06:40:12Z",
            source_url="https://ibjarates.com",
        )
        assert is_new is False
        assert is_revised is True
        assert r3.revision == 2
        assert r3.price_inr == 98600.0

        # Old record marked superseded
        old_rec = await repo.get_by_id(r1.id)
        assert old_rec.status == RateStatus.SUPERSEDED.value

        # Latest returns revision 2
        latest = await repo.get_latest_rate("silver", "999")
        assert latest.revision == 2
        assert latest.price_inr == 98600.0
