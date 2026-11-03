import csv
import io
import secrets
from datetime import datetime, date
from typing import Literal
from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.time_utils import now_ist
from app.domain.metal import Session, RateStatus
from app.domain.schemas import (
    DateRatesResponse,
    PaginatedRatesResponse,
    RateItemSummary,
    SilverRate,
)
from app.events.sse_bus import sse_bus
from app.scheduler.staleness import compute_staleness
from app.storage.database import get_connection
from app.storage.repository import RateRecord, RateRepository
from app.validation.quarantine import QuarantineManager

router = APIRouter(prefix="/silver", tags=["silver"])


_to_silver_rate_dto = SilverRate.from_record


def _to_rate_summary(rec: RateRecord | None, include_gst: bool = False) -> RateItemSummary | None:
    if rec is None:
        return None
    price_kg = rec.price_inr
    derived = False
    excludes_gst = True
    if include_gst:
        price_kg = round(price_kg * 1.03, 2)
        derived = True
        excludes_gst = False

    return RateItemSummary(
        price_inr_per_kg=price_kg,
        price_inr_per_10g=round(price_kg / 100.0, 2),
        price_inr_per_gram=round(price_kg / 1000.0, 4),
        status=RateStatus(rec.status),
        revision=rec.revision,
        detected_at=rec.first_seen_at,
        excludes_gst=excludes_gst,
        derived=derived,
    )


@router.get("/latest", response_model=SilverRate)
async def get_latest_silver(request: Request, include_gst: bool = Query(False)):
    """
    Get the most recent valid published Silver 999 rate with computed conversions and staleness.
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    calendar_holidays = scheduler.holiday_calendar.holidays if scheduler else set()
    parser_healthy = scheduler.parser_healthy if scheduler else True

    async with get_connection() as conn:
        repo = RateRepository(conn)
        latest = await repo.get_latest_rate(metal="silver", purity="999")

    if not latest:
        raise HTTPException(status_code=404, detail="No silver rate published yet")

    now_dt = now_ist()
    is_stale, stale_reason, next_pub = compute_staleness(
        latest_rate=latest,
        now_ist_dt=now_dt,
        holiday_calendar=calendar_holidays,
        scheduler_healthy=parser_healthy,
        last_scrape_failed=bool(scheduler and scheduler.last_error),
    )

    return _to_silver_rate_dto(
        rec=latest,
        include_gst=include_gst,
        is_stale=is_stale,
        stale_reason=stale_reason,
        next_expected_pub=next_pub,
    )


@router.get("/stream")
async def silver_rate_stream():
    """
    Server-Sent Events endpoint pushing live events:
    - rate.published
    - rate.revised
    - ping (keepalive every 15s)
    """
    if not sse_bus.has_capacity():
        raise HTTPException(status_code=503, detail="Maximum SSE subscriber limit reached")
    return StreamingResponse(
        sse_bus.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/quarantine", response_model=list[SilverRate])
async def list_quarantined_silver():
    """
    List all Silver 999 records currently held in quarantine.
    """
    async with get_connection() as conn:
        q_manager = QuarantineManager(conn)
        records = await q_manager.list_quarantined()
    return [_to_silver_rate_dto(r) for r in records if r.metal == "silver"]


def _verify_admin_access(request: Request, x_admin_token: str | None) -> None:
    """Require X-Admin-Token when configured; otherwise allow loopback clients only."""
    if settings.admin_token:
        if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
            raise HTTPException(status_code=403, detail="Invalid or missing admin token")
        return
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost", "testclient"):
        raise HTTPException(status_code=403, detail="Admin token required for remote quarantine approval")


@router.post("/quarantine/{rate_id}/approve")
async def approve_quarantined_silver(
    rate_id: int,
    request: Request,
    x_admin_token: str | None = Header(default=None),
):
    """
    Manually approve a quarantined rate, converting its status to valid.
    """
    _verify_admin_access(request, x_admin_token)
    async with get_connection() as conn:
        q_manager = QuarantineManager(conn)
        approved = await q_manager.approve_record(rate_id)
    if not approved:
        raise HTTPException(status_code=404, detail=f"Quarantined record {rate_id} not found or already valid")
    return {"status": "approved", "rate_id": rate_id}


@router.get("/{rate_date}", response_model=DateRatesResponse)
async def get_silver_by_date(rate_date: str, include_gst: bool = Query(False)):
    """
    Get AM and PM rates for a specific calendar date (YYYY-MM-DD).
    """
    try:
        date.fromisoformat(rate_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{rate_date}'. Expected YYYY-MM-DD",
        )

    async with get_connection() as conn:
        repo = RateRepository(conn)
        rates = await repo.get_rates_by_date(rate_date, metal="silver", purity="999")

    if not rates:
        raise HTTPException(
            status_code=404,
            detail=f"No silver rates found for date {rate_date}",
        )

    am_rec = next((r for r in rates if r.session == "AM"), None)
    pm_rec = next((r for r in rates if r.session == "PM"), None)

    return DateRatesResponse(
        rate_date=rate_date,
        am=_to_rate_summary(am_rec, include_gst=include_gst),
        pm=_to_rate_summary(pm_rec, include_gst=include_gst),
    )


@router.get("", response_model=PaginatedRatesResponse)
async def get_silver_range(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    session: Session | None = None,
    format: Literal["json", "csv"] = "json",
    limit: int = Query(50, ge=1, le=366),
    offset: int = Query(0, ge=0),
):
    """
    Paginated range query for historical silver rates. Supports format=json or format=csv.
    """
    if from_date:
        try:
            date.fromisoformat(from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'from' date format")
    if to_date:
        try:
            date.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'to' date format")

    session_val = session.value if session else None

    async with get_connection() as conn:
        repo = RateRepository(conn)
        items, total = await repo.get_rates_range(
            from_date=from_date,
            to_date=to_date,
            session=session_val,
            metal="silver",
            purity="999",
            limit=limit,
            offset=offset,
        )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "rate_date",
            "session",
            "metal",
            "purity",
            "price_inr_per_kg",
            "price_inr_per_10g",
            "price_inr_per_gram",
            "revision",
            "detected_at",
        ])
        for item in items:
            writer.writerow([
                item.rate_date,
                item.session,
                item.metal,
                item.purity,
                item.price_inr,
                round(item.price_inr / 100.0, 2),
                round(item.price_inr / 1000.0, 4),
                item.revision,
                item.first_seen_at,
            ])
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=silver_rates.csv"},
        )

    dtos = [_to_silver_rate_dto(item) for item in items]
    return PaginatedRatesResponse(
        items=dtos,
        total=total,
        limit=limit,
        offset=offset,
    )
