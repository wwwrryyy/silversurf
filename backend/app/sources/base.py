from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from app.domain.metal import Metal, Session


@dataclass(frozen=True)
class RawScrapeResult:
    rate_date: date
    session: Session
    metal: Metal
    purity: str
    price_inr: float
    unit: str
    raw_html_bytes: bytes
    http_status: int
    source_url: str
    card_price_inr: float | None = None


@runtime_checkable
class RateSource(Protocol):
    async def fetch_latest(self) -> list[RawScrapeResult]:
        """Fetch current tables from the source."""
        ...

    async def fetch_historical_pdf(self, pdf_url: str) -> list[RawScrapeResult]:
        """Fetch and parse 30-day historical rates from PDF."""
        ...
