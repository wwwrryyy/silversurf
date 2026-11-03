import asyncio
import logging
import random
import re
from datetime import date
from typing import Any
import httpx
from selectolax.lexbor import LexborHTMLParser as HTMLParser, LexborNode as Node

from app.config import settings
from app.core.errors import ParserIntegrityError, SourceFetchError
from app.core.time_utils import parse_dd_mm_yyyy_ist
from app.domain.metal import Metal, Session
from app.sources.base import RawScrapeResult

logger = logging.getLogger(__name__)


class IbjaHtmlSource:
    def __init__(
        self,
        source_url: str | None = None,
        user_agent: str | None = None,
        timeout: float | None = None,
    ):
        self.source_url = source_url or settings.source_url
        self.user_agent = user_agent or settings.user_agent
        self.timeout = timeout or settings.request_timeout_seconds
        self._etag: str | None = None
        self._last_modified: str | None = None

    async def fetch_latest(self) -> list[RawScrapeResult]:
        """Fetch raw HTML from ibjarates.com and parse rates."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if self._etag:
            headers["If-None-Match"] = self._etag
        if self._last_modified:
            headers["If-Modified-Since"] = self._last_modified

        response = None
        last_exc: Exception | None = None
        for attempt in range(3):
            delay = min(2 ** attempt + random.uniform(0.1, 0.5), 10.0)
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(self.source_url, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                response = None
            else:
                if response.status_code != 429 and response.status_code < 500:
                    break
                retry_after = response.headers.get("retry-after", "")
                if retry_after.isdigit():
                    delay = min(float(retry_after), 30.0)
            if attempt < 2:
                logger.warning("Fetch attempt %d failed; retrying in %.1fs", attempt + 1, delay)
                await asyncio.sleep(delay)

        if response is None:
            logger.error(f"Failed to fetch {self.source_url}: {last_exc}")
            raise SourceFetchError(f"HTTP request to {self.source_url} failed: {last_exc}") from last_exc

        if response.status_code == 304:
            logger.info("IBJA rates page not modified (304)")
            return []

        if response.status_code != 200:
            raise SourceFetchError(
                f"Source returned non-200 status code: {response.status_code}"
            )

        # Update cache headers
        if "etag" in response.headers:
            self._etag = response.headers["etag"]
        if "last-modified" in response.headers:
            self._last_modified = response.headers["last-modified"]

        raw_bytes = response.content
        if len(raw_bytes) > settings.max_http_response_bytes:
            raise SourceFetchError(f"Response exceeds {settings.max_http_response_bytes} bytes")
        return self.parse_html(raw_bytes, http_status=response.status_code, source_url=self.source_url)

    def parse_html(
        self, raw_bytes: bytes, http_status: int = 200, source_url: str = ""
    ) -> list[RawScrapeResult]:
        """
        Parse raw HTML bytes using selectolax.
        Enforces strict header-based parsing for 'Silver 999'.
        """
        text = raw_bytes.decode("utf-8", errors="replace")
        parser = HTMLParser(text)

        # Cross-check: Look for hero/card silver rate if present
        card_silver_price = self._extract_card_silver_price(parser)

        # Locate tables
        tables = parser.css("table")
        results: list[RawScrapeResult] = []
        silver_tables_found = 0

        # We keep track of detected tables with Silver 999
        candidate_tables: list[tuple[Node, Session | None, list[tuple[int, Session | None]], int, Node | None]] = []

        for table in tables:
            # Skip wrapper/layout tables that contain nested tables
            if len(table.css("table")) > 1:
                continue

            session = self._detect_table_session(table)
            header_info = self._find_header_row_info(table)
            if not header_info:
                continue

            header_tr, headers = header_info
            silver_cols = self._find_silver_columns(headers)
            if silver_cols:
                date_idx = self._find_date_col_idx(headers)
                silver_tables_found += 1
                candidate_tables.append((table, session, silver_cols, date_idx, header_tr))

        if silver_tables_found == 0:
            raise ParserIntegrityError("No tables containing 'Silver 999' column header found")

        # If session wasn't explicitly labeled on tables, infer by order (1st = AM, 2nd = PM)
        if len(candidate_tables) >= 2 and all(s is None for _, s, _, _, _ in candidate_tables[:2]):
            first = candidate_tables[0]
            second = candidate_tables[1]
            candidate_tables = [
                (first[0], Session.AM, first[2], first[3], first[4]),
                (second[0], Session.PM, second[2], second[3], second[4]),
            ] + candidate_tables[2:]
        elif len(candidate_tables) == 1 and candidate_tables[0][1] is None:
            first = candidate_tables[0]
            candidate_tables = [(first[0], Session.AM, first[2], first[3], first[4])]

        for table, session, silver_cols, date_idx, header_tr in candidate_tables:
            effective_session = session or Session.AM
            table_results = self._parse_table_rows(
                table=table,
                session=effective_session,
                silver_cols=silver_cols,
                date_idx=date_idx,
                header_tr=header_tr,
                raw_bytes=raw_bytes,
                http_status=http_status,
                source_url=source_url,
                card_price=card_silver_price,
            )
            results.extend(table_results)

        if not results:
            raise ParserIntegrityError("Found 'Silver 999' header but zero valid data rows")

        return results

    def _find_header_row_info(self, table: Node) -> tuple[Node, list[str]] | None:
        """
        Locate the specific header <tr> row that contains precious metal column headers,
        expanding any colspan attributes so that column indices map 1-to-1 to <td> cells.
        """
        # First check thead tr rows, then all tr rows
        rows = table.css("thead tr") or table.css("tr")
        for tr in rows:
            cells = tr.css("th") or tr.css("td")
            if not cells:
                continue

            texts = [c.text(strip=True) for c in cells]
            # Check if this row looks like a metal header row
            has_silver = any("silver" in t.lower() for t in texts)
            has_gold = any("gold" in t.lower() for t in texts)
            has_date = any("date" in t.lower() for t in texts)

            if has_silver or (has_date and has_gold):
                expanded: list[str] = []
                for c in cells:
                    colspan_str = c.attributes.get("colspan", "1")
                    try:
                        colspan = int(colspan_str)
                    except ValueError:
                        colspan = 1
                    t = c.text(strip=True)
                    for _ in range(max(1, colspan)):
                        expanded.append(t)
                return tr, expanded
        return None

    def _find_silver_columns(self, headers: list[str]) -> list[tuple[int, Session | None]]:
        """
        Find 0-based column indices matching 'Silver 999' or 'Silver'.
        Returns list of (column_idx, explicit_session_or_none).
        Guarantees never matching platinum, gold, or other metals.
        """
        cols: list[tuple[int, Session | None]] = []
        for idx, text in enumerate(headers):
            clean = re.sub(r"\s+", " ", text).strip().lower()
            # Must contain silver, and must NOT contain platinum or gold
            if "silver" in clean and "999" in clean and "platinum" not in clean and "gold" not in clean and "pt" not in clean:
                session: Session | None = None
                if "am" in clean or "open" in clean:
                    session = Session.AM
                elif "pm" in clean or "close" in clean:
                    session = Session.PM
                cols.append((idx, session))
        return cols

    def _find_date_col_idx(self, headers: list[str]) -> int:
        """Find the column index for date, defaulting to 0."""
        for idx, text in enumerate(headers):
            clean = text.strip().lower()
            if "date" in clean:
                return idx
        return 0

    def _detect_table_session(self, table: Node) -> Session | None:
        """Detect whether table is Opening (AM) or Closing (PM)."""
        # 1. Check table attributes (id, class)
        attrs = " ".join([table.attributes.get("id", ""), table.attributes.get("class", "")]).lower()
        if "closing" in attrs or "pm" in attrs:
            return Session.PM
        if "opening" in attrs or "am" in attrs:
            return Session.AM

        # 2. Check caption or previous header tags
        caption = table.css_first("caption")
        if caption:
            cap_text = caption.text().lower()
            if "closing" in cap_text or "pm" in cap_text:
                return Session.PM
            if "opening" in cap_text or "am" in cap_text:
                return Session.AM

        # Check preceding headings in DOM
        prev = table.prev
        count = 0
        while prev and count < 5:
            if prev.tag in ("h1", "h2", "h3", "h4", "h5", "div", "p"):
                txt = prev.text().lower()
                if "closing" in txt or "pm" in txt:
                    return Session.PM
                if "opening" in txt or "am" in txt:
                    return Session.AM
            prev = prev.prev
            count += 1

        # Check parent container
        parent = table.parent
        if parent:
            parent_attrs = " ".join([parent.attributes.get("id", ""), parent.attributes.get("class", "")]).lower()
            if "closing" in parent_attrs or "pm" in parent_attrs:
                return Session.PM
            if "opening" in parent_attrs or "am" in parent_attrs:
                return Session.AM

        return None

    def _parse_table_rows(
        self,
        table: Node,
        session: Session,
        silver_cols: list[tuple[int, Session | None]],
        date_idx: int,
        header_tr: Node | None,
        raw_bytes: bytes,
        http_status: int,
        source_url: str,
        card_price: float | None,
    ) -> list[RawScrapeResult]:
        """Extract data rows for a verified table."""
        rows = table.css("tbody tr")
        if not rows:
            all_rows = table.css("tr")
            rows = [r for r in all_rows if r != header_tr]

        results: list[RawScrapeResult] = []

        for row in rows:
            if row == header_tr:
                continue

            cells = row.css("td, th")
            if len(cells) <= date_idx:
                continue

            date_str = cells[date_idx].text(strip=True)
            try:
                rate_date = parse_dd_mm_yyyy_ist(date_str)
            except Exception:
                # Row might be a subheader or malformed date, skip
                continue

            for col_idx, explicit_session in silver_cols:
                if len(cells) <= col_idx:
                    continue

                silver_str = cells[col_idx].text(strip=True)
                price = self._parse_price(silver_str)
                if price is None:
                    continue

                target_session = explicit_session or session

                results.append(
                    RawScrapeResult(
                        rate_date=rate_date,
                        session=target_session,
                        metal=Metal.SILVER,
                        purity="999",
                        price_inr=price,
                        unit="per_kg",
                        raw_html_bytes=raw_bytes,
                        http_status=http_status,
                        source_url=source_url,
                        card_price_inr=card_price,
                    )
                )

        return results

    def _parse_price(self, price_str: str) -> float | None:
        """Parse clean float price from string like '98,500' or '98500.00'."""
        cleaned = re.sub(r"[^\d.]", "", price_str.strip())
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_card_silver_price(self, parser: HTMLParser) -> float | None:
        """Extract silver price from hero card/widget if present."""
        cards = parser.css(".card, .widget, .rate-card, .box, div")
        pattern = r"silver(?:\s*999)?[:\s\-\–]*(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]{4,7}(?:\.[0-9]{1,2})?)"
        for card in cards:
            text = card.text()
            if "silver" in text.lower():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parsed = self._parse_price(match.group(1))
                    if parsed and parsed > 1000:
                        return parsed
        return None

    async def fetch_historical_pdf(self, pdf_url: str) -> list[RawScrapeResult]:
        """Delegate to IbjaPdfBackfillSource."""
        from app.sources.ibja_pdf import IbjaPdfBackfillSource
        pdf_source = IbjaPdfBackfillSource()
        return await pdf_source.fetch_historical_pdf(pdf_url)
