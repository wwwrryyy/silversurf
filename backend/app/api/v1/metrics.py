from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from app.storage.database import get_connection
from app.storage.repository import RateRepository

router = APIRouter(tags=["metrics"])

SCRAPE_TOTAL = Counter(
    "silversurf_scrape_total",
    "Total number of scraper executions",
    ["outcome"],
)

LATEST_RATE_GAUGE = Gauge(
    "silversurf_latest_silver_rate_inr_per_kg",
    "Latest valid silver benchmark rate in INR per kg",
    ["session"],
)

QUARANTINE_GAUGE = Gauge(
    "silversurf_quarantined_records_count",
    "Count of currently quarantined rate records",
)

PARSER_HEALTH_GAUGE = Gauge(
    "silversurf_parser_healthy",
    "1 if HTML parser integrity is healthy, 0 if failing",
)


@router.get("/metrics")
async def get_metrics(request: Request):
    """
    Prometheus metrics export endpoint.
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        PARSER_HEALTH_GAUGE.set(1 if scheduler.parser_healthy else 0)

    async with get_connection() as conn:
        repo = RateRepository(conn)
        latest = await repo.get_latest_rate("silver", "999")
        if latest:
            LATEST_RATE_GAUGE.labels(session=latest.session).set(latest.price_inr)
        q_count = await repo.get_quarantined_count()
        QUARANTINE_GAUGE.set(q_count)

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
