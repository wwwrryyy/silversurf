import asyncio
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import logging
from typing import Any

from app.config import settings
from app.core.errors import ParserIntegrityError, SourceFetchError
from app.core.time_utils import now_ist, now_utc, parse_hhmm, to_utc_iso
from app.domain.metal import Metal, RateStatus, SchedulerMode, Session
from app.domain.schemas import SilverRate
from app.events.sse_bus import sse_bus
from app.scheduler.calendar import HolidayCalendar
from app.sources.base import RateSource, RawScrapeResult
from app.sources.ibja_html import IbjaHtmlSource
from app.sources.playwright import PlaywrightFallbackSource
from app.storage.database import get_connection
from app.storage.repository import RateRecord, RateRepository
from app.storage.snapshots import SnapshotManager
from app.validation.rules import ValidationPipeline

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Enforces strict egress cap: <= max_requests per window_seconds."""

    def __init__(self, max_requests: int = 2, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            # Clean timestamps older than window
            self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
            if len(self.timestamps) >= self.max_requests:
                sleep_time = self.window_seconds - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    logger.debug("Rate limit reached. Sleeping for %.2f seconds", sleep_time)
                    await asyncio.sleep(sleep_time)
                now = loop.time()
                self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
            self.timestamps.append(now)


@dataclass
class ScrapeSummary:
    outcome: str  # 'success', 'no_change', 'error', 'quarantined'
    records_new: int
    records_changed: int
    error: str | None = None


class AdaptiveScheduler:
    def __init__(
        self,
        db_path: str | None = None,
        snapshots_dir: str | None = None,
        holiday_calendar: HolidayCalendar | None = None,
        html_source: RateSource | None = None,
        fallback_source: RateSource | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
    ):
        self.db_path = db_path or settings.database_path
        self.holiday_calendar = holiday_calendar or HolidayCalendar()
        self.snapshot_manager = SnapshotManager(snapshots_dir)
        self.primary_source = html_source or IbjaHtmlSource()
        self.fallback_source = fallback_source or PlaywrightFallbackSource()
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter(
            max_requests=settings.rate_limit_per_minute, window_seconds=60.0
        )
        self.validator = ValidationPipeline()

        # Operational state
        self.consecutive_parser_failures = 0
        self.last_successful_scrape: str | None = None
        self.last_error: str | None = None
        self._last_prune_date: date | None = None
        self.is_running = False
        self._task: asyncio.Task | None = None

    @property
    def parser_healthy(self) -> bool:
        return self.consecutive_parser_failures < 3

    def determine_mode(
        self,
        now_ist_dt: datetime,
        session_am_captured: bool = False,
        session_pm_captured: bool = False,
    ) -> SchedulerMode:
        """
        Pure deterministic scheduler state machine calculation.
        """
        today = now_ist_dt.date()
        is_weekend = now_ist_dt.weekday() >= 5
        is_holiday = self.holiday_calendar.is_holiday(today)

        if is_weekend or is_holiday:
            return SchedulerMode.OFF_DAY

        cur_time = now_ist_dt.time()

        # Time markers
        am_hot_start = parse_hhmm(settings.hot_window_am_start)
        am_hot_end = parse_hhmm(settings.hot_window_am_end)
        am_catchup_start = (datetime.combine(today, am_hot_end) - timedelta(minutes=5)).time()
        am_catchup_end = (datetime.combine(today, am_hot_end) + timedelta(hours=2)).time()

        pm_hot_start = parse_hhmm(settings.hot_window_pm_start)
        pm_hot_end = parse_hhmm(settings.hot_window_pm_end)
        pm_catchup_start = (datetime.combine(today, pm_hot_end) - timedelta(minutes=5)).time()
        pm_catchup_end = (datetime.combine(today, pm_hot_end) + timedelta(hours=2)).time()

        # Check AM window
        if am_hot_start <= cur_time <= am_catchup_end:
            if session_am_captured:
                return SchedulerMode.IDLE
            if cur_time >= am_catchup_start:
                return SchedulerMode.CATCH_UP
            return SchedulerMode.HOT

        # Check PM window
        if pm_hot_start <= cur_time <= pm_catchup_end:
            if session_pm_captured:
                return SchedulerMode.IDLE
            if cur_time >= pm_catchup_start:
                return SchedulerMode.CATCH_UP
            return SchedulerMode.HOT

        return SchedulerMode.IDLE

    def get_poll_interval_seconds(self, mode: SchedulerMode) -> int:
        match mode:
            case SchedulerMode.HOT:
                return settings.hot_poll_interval_seconds
            case SchedulerMode.CATCH_UP:
                return settings.catch_up_poll_interval_seconds
            case SchedulerMode.IDLE:
                return settings.idle_poll_interval_seconds
            case SchedulerMode.OFF_DAY:
                return settings.off_day_poll_interval_seconds

    async def poll_once(self, current_time_ist: datetime | None = None) -> ScrapeSummary:
        """
        Execute a single end-to-end scrape cycle.
        """
        start_time_iso = to_utc_iso(now_utc()) or ""
        now_dt = current_time_ist or now_ist()

        # Rate limiter
        await self.rate_limiter.acquire()

        # Source selection
        use_fallback = self.consecutive_parser_failures >= 2
        active_source = self.fallback_source if use_fallback else self.primary_source

        try:
            raw_results = await active_source.fetch_latest()
        except Exception as exc:
            logger.error("Scraper fetch failure: %s", exc)
            self.consecutive_parser_failures += 1
            self.last_error = str(exc)
            finish_time_iso = to_utc_iso(now_utc()) or ""
            async with get_connection(self.db_path) as conn:
                repo = RateRepository(conn)
                await repo.record_scrape_run(
                    started_at=start_time_iso,
                    finished_at=finish_time_iso,
                    outcome="error",
                    records_new=0,
                    records_changed=0,
                    error_message=str(exc),
                )
            return ScrapeSummary(outcome="error", records_new=0, records_changed=0, error=str(exc))

        # Check V4 integrity
        if not raw_results:
            # 304 or empty response without error
            finish_time_iso = to_utc_iso(now_utc()) or ""
            async with get_connection(self.db_path) as conn:
                repo = RateRepository(conn)
                await repo.record_scrape_run(
                    started_at=start_time_iso,
                    finished_at=finish_time_iso,
                    outcome="no_change",
                    records_new=0,
                    records_changed=0,
                )
            return ScrapeSummary(outcome="no_change", records_new=0, records_changed=0)

        # Successful fetch - reset parser failures
        self.consecutive_parser_failures = 0
        self.last_error = None
        finish_time_iso = to_utc_iso(now_utc()) or ""
        self.last_successful_scrape = finish_time_iso

        records_new = 0
        records_changed = 0
        has_quarantined = False
        snapshot_id: str | None = None

        # Sort raw_results chronologically (oldest to newest)
        # so historical backfill or first scrape seeds history sequentially
        raw_results.sort(key=lambda r: (r.rate_date, 0 if r.session == Session.AM else 1))

        async with get_connection(self.db_path) as conn:
            repo = RateRepository(conn)

            for item in raw_results:
                # Get previous day rate for DoD rule V2
                prev_rate = await repo.get_previous_valid_rate(
                    before_date=item.rate_date.isoformat(),
                    metal=item.metal.value,
                    purity=item.purity,
                )
                prev_price = None
                if prev_rate:
                    # Only apply DoD check if the previous rate is within 7 calendar days
                    prev_dt = date.fromisoformat(prev_rate.rate_date)
                    if (item.rate_date - prev_dt).days <= 7:
                        prev_price = prev_rate.price_inr

                val_result = self.validator.validate_record(
                    record=item,
                    prev_price_inr=prev_price,
                    current_time_ist=now_dt,
                )

                if not val_result.is_valid:
                    logger.warning("Record failed validation: %s", val_result.error_message)
                    continue

                if val_result.status == RateStatus.QUARANTINED:
                    has_quarantined = True

                # Check if this record creates a new or revised entry before saving snapshot
                # If we don't have a snapshot_id yet and this produces changes, save snapshot
                detected_at_iso = to_utc_iso(now_utc()) or ""

                record, is_new, is_revised = await repo.save_rate(
                    rate_date=item.rate_date.isoformat(),
                    session=item.session.value,
                    metal=item.metal.value,
                    purity=item.purity,
                    price_inr=item.price_inr,
                    unit=item.unit,
                    status=val_result.status.value,
                    first_seen_at=detected_at_iso,
                    source_url=item.source_url,
                    snapshot_id=snapshot_id,
                )

                if is_new or is_revised:
                    if is_new:
                        records_new += 1
                    if is_revised:
                        records_changed += 1

                    # Save raw snapshot on disk if not saved yet for this run
                    if snapshot_id is None and item.raw_html_bytes:
                        snapshot_id = await self.snapshot_manager.save_snapshot(
                            conn=conn,
                            raw_bytes=item.raw_html_bytes,
                            http_status=item.http_status,
                        )
                        # Link snapshot_id to the record
                        await conn.execute(
                            "UPDATE rates SET snapshot_id = ? WHERE id = ?",
                            (snapshot_id, record.id),
                        )
                        await conn.commit()

                    # Emit SSE event
                    if val_result.status == RateStatus.VALID:
                        silver_dto = self._record_to_dto(record)
                        event_type = "rate.published" if is_new else "rate.revised"
                        await sse_bus.publish(event_type, silver_dto.model_dump())

            outcome = "quarantined" if has_quarantined else ("success" if (records_new > 0 or records_changed > 0) else "no_change")
            await repo.record_scrape_run(
                started_at=start_time_iso,
                finished_at=finish_time_iso,
                outcome=outcome,
                records_new=records_new,
                records_changed=records_changed,
            )

        return ScrapeSummary(
            outcome=outcome,
            records_new=records_new,
            records_changed=records_changed,
        )

    def _record_to_dto(self, record: RateRecord) -> SilverRate:
        return SilverRate.from_record(record)

    async def get_current_mode(self) -> SchedulerMode:
        """Evaluate current mode against the database state for today."""
        now_dt = now_ist()
        today_str = now_dt.date().isoformat()
        session_am = False
        session_pm = False

        async with get_connection(self.db_path) as conn:
            repo = RateRepository(conn)
            rates = await repo.get_rates_by_date(today_str)
            for r in rates:
                if r.session == "AM":
                    session_am = True
                elif r.session == "PM":
                    session_pm = True

        return self.determine_mode(now_dt, session_am, session_pm)

    async def start(self) -> None:
        """Start the background scheduling worker loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("AdaptiveScheduler background worker started")

    async def stop(self) -> None:
        """Stop the background worker."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AdaptiveScheduler stopped")

    async def _worker_loop(self) -> None:
        while self.is_running:
            try:
                mode = await self.get_current_mode()
                poll_interval = self.get_poll_interval_seconds(mode)
                await self.poll_once()
                await self._prune_daily()
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in scheduler worker loop: %s", exc)
                await asyncio.sleep(10)

    async def _prune_daily(self) -> None:
        """Prune expired snapshots/scrape runs at most once per IST day."""
        today = now_ist().date()
        if self._last_prune_date == today:
            return
        async with get_connection(self.db_path) as conn:
            await self.snapshot_manager.prune_expired(conn)
        self._last_prune_date = today
