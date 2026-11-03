from fastapi import APIRouter, Request

from app.core.time_utils import now_ist
from app.domain.metal import SchedulerMode
from app.domain.schemas import HealthStatus
from app.storage.database import get_connection
from app.storage.repository import RateRepository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def get_health(request: Request):
    """
    Operational health endpoint: scheduler state, parser status, last scrape, quarantined count.
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    parser_healthy = scheduler.parser_healthy if scheduler else True
    scheduler_mode = await scheduler.get_current_mode() if scheduler else SchedulerMode.IDLE
    last_scrape = scheduler.last_successful_scrape if scheduler else None

    async with get_connection() as conn:
        repo = RateRepository(conn)
        if not last_scrape:
            last_scrape = await repo.get_last_successful_scrape()
        quarantined_count = await repo.get_quarantined_count()

    overall_status = "healthy"
    if not parser_healthy:
        overall_status = "unhealthy"
    elif quarantined_count > 0:
        overall_status = "degraded"

    now_ist_str = now_ist().isoformat()

    return HealthStatus(
        status=overall_status,  # type: ignore[arg-type]
        scheduler_mode=scheduler_mode,
        last_successful_scrape=last_scrape,
        parser_healthy=parser_healthy,
        quarantined_records_count=quarantined_count,
        current_time_ist=now_ist_str,
    )
