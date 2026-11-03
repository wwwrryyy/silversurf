import io
import logging
import re
from pathlib import Path
from urllib.parse import urlparse
import httpx
import pdfplumber

from app.config import settings
from app.core.errors import ParserIntegrityError, SourceFetchError
from app.core.time_utils import parse_dd_mm_yyyy_ist
from app.domain.metal import Metal, Session
from app.sources.base import RawScrapeResult

logger = logging.getLogger(__name__)


class IbjaPdfBackfillSource:
    def __init__(self, user_agent: str | None = None, timeout: float | None = None):
        self.user_agent = user_agent or settings.user_agent
        self.timeout = timeout or settings.request_timeout_seconds

    async def fetch_historical_pdf(self, pdf_url_or_path: str) -> list[RawScrapeResult]:
        """Fetch PDF from URL or local path and extract 30-day historical rates."""
        if pdf_url_or_path.startswith("http://") or pdf_url_or_path.startswith("https://"):
            parsed = urlparse(pdf_url_or_path)
            if parsed.hostname not in settings.allowed_scrape_hosts:
                raise SourceFetchError(f"PDF host not allowed: {parsed.hostname}")
            try:
                headers = {"User-Agent": self.user_agent}
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(pdf_url_or_path, headers=headers)
                    if resp.status_code != 200:
                        raise SourceFetchError(
                            f"PDF fetch returned status {resp.status_code}"
                        )
                    pdf_bytes = resp.content
                    if len(pdf_bytes) > settings.max_http_response_bytes:
                        raise SourceFetchError("PDF exceeds maximum allowed size")
            except Exception as exc:
                raise SourceFetchError(f"Failed to fetch PDF from {pdf_url_or_path}: {exc}") from exc
        else:
            path = Path(pdf_url_or_path)
            if not path.exists():
                raise SourceFetchError(f"Local PDF file not found: {pdf_url_or_path}")
            if path.stat().st_size > settings.max_http_response_bytes:
                raise SourceFetchError("Local PDF exceeds maximum allowed size")
            pdf_bytes = path.read_bytes()

        return self.parse_pdf(pdf_bytes, source_url=pdf_url_or_path)

    def parse_pdf(self, pdf_bytes: bytes, source_url: str = "") -> list[RawScrapeResult]:
        """Extract Silver 999 rates from PDF bytes using pdfplumber."""
        results: list[RawScrapeResult] = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # Header row
                        header_row = [str(col).strip() if col else "" for col in table[0]]
                        silver_idx = self._find_silver_col_idx(header_row)
                        if silver_idx is None:
                            continue

                        date_idx = self._find_date_col_idx(header_row)
                        session_idx = self._find_session_col_idx(header_row)

                        for row in table[1:]:
                            if len(row) <= silver_idx:
                                continue

                            date_text = str(row[date_idx]).strip() if date_idx < len(row) and row[date_idx] else ""
                            silver_text = str(row[silver_idx]).strip() if row[silver_idx] else ""

                            try:
                                rate_date = parse_dd_mm_yyyy_ist(date_text)
                            except Exception:
                                continue

                            price = self._parse_price(silver_text)
                            if price is None:
                                continue

                            # Detect session from session col or default to AM/PM based on context
                            session = Session.AM
                            if session_idx is not None and session_idx < len(row) and row[session_idx]:
                                s_text = str(row[session_idx]).upper()
                                if "PM" in s_text or "CLOS" in s_text:
                                    session = Session.PM
                                elif "AM" in s_text or "OPEN" in s_text:
                                    session = Session.AM

                            results.append(
                                RawScrapeResult(
                                    rate_date=rate_date,
                                    session=session,
                                    metal=Metal.SILVER,
                                    purity="999",
                                    price_inr=price,
                                    unit="per_kg",
                                    raw_html_bytes=pdf_bytes,
                                    http_status=200,
                                    source_url=source_url,
                                )
                            )
        except Exception as exc:
            logger.error(f"Failed to parse PDF: {exc}")
            raise ParserIntegrityError(f"PDF parsing error: {exc}") from exc

        return results

    def _find_silver_col_idx(self, headers: list[str]) -> int | None:
        for idx, text in enumerate(headers):
            clean = re.sub(r"\s+", " ", text).strip().lower()
            if "silver 999" in clean or ("silver" in clean and "999" in clean):
                return idx
        return None

    def _find_date_col_idx(self, headers: list[str]) -> int:
        for idx, text in enumerate(headers):
            if "date" in text.lower():
                return idx
        return 0

    def _find_session_col_idx(self, headers: list[str]) -> int | None:
        for idx, text in enumerate(headers):
            clean = text.lower()
            if "session" in clean or "type" in clean or "time" in clean:
                return idx
        return None

    def _parse_price(self, price_str: str) -> float | None:
        cleaned = re.sub(r"[^\d.]", "", price_str.strip())
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    async def fetch_latest(self) -> list[RawScrapeResult]:
        raise NotImplementedError("IbjaPdfBackfillSource only supports fetch_historical_pdf")
