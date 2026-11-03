from datetime import date
from typing import Literal
from pydantic import BaseModel, Field

from app.domain.metal import Metal, Session, RateStatus, SchedulerMode


class RateItemSummary(BaseModel):
    price_inr_per_kg: float
    price_inr_per_10g: float
    price_inr_per_gram: float
    status: RateStatus
    revision: int
    detected_at: str
    excludes_gst: bool = True
    derived: bool = False


class DateRatesResponse(BaseModel):
    rate_date: str
    am: RateItemSummary | None = None
    pm: RateItemSummary | None = None


class SilverRate(BaseModel):
    metal: Metal = Metal.SILVER
    purity: str = "999"
    rate_date: str
    session: Session
    price_inr_per_kg: float
    price_inr_per_10g: float
    price_inr_per_gram: float
    excludes_gst: bool = True
    derived: bool = False
    detected_at: str
    revision: int = 1
    stale: bool = False
    stale_reason: Literal["source_unavailable", "parser_unhealthy", "not_yet_published"] | None = None
    next_expected_publication: str | None = None
    source: str = "ibjarates.com"
    attribution: str = "Source: IBJA (ibjarates.com)"

    @classmethod
    def from_record(
        cls,
        rec,
        include_gst: bool = False,
        is_stale: bool = False,
        stale_reason: str | None = None,
        next_expected_pub: str | None = None,
    ) -> "SilverRate":
        """Build the API DTO from a stored RateRecord (single conversion path)."""
        price_kg = rec.price_inr
        if include_gst:
            price_kg = round(price_kg * 1.03, 2)
        return cls(
            metal=Metal(rec.metal),
            purity=rec.purity,
            rate_date=rec.rate_date,
            session=Session(rec.session),
            price_inr_per_kg=price_kg,
            price_inr_per_10g=round(price_kg / 100.0, 2),
            price_inr_per_gram=round(price_kg / 1000.0, 4),
            excludes_gst=not include_gst,
            derived=include_gst,
            detected_at=rec.first_seen_at,
            revision=rec.revision,
            stale=is_stale,
            stale_reason=stale_reason,  # type: ignore[arg-type]
            next_expected_publication=next_expected_pub,
        )


class PaginatedRatesResponse(BaseModel):
    items: list[SilverRate]
    total: int
    limit: int
    offset: int


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    scheduler_mode: SchedulerMode
    last_successful_scrape: str | None = None
    parser_healthy: bool
    quarantined_records_count: int
    current_time_ist: str


class SSERateEvent(BaseModel):
    event: Literal["rate.published", "rate.revised", "ping"]
    data: SilverRate | dict
