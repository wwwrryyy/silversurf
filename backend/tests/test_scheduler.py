import asyncio
from datetime import date, datetime
import time
from zoneinfo import ZoneInfo
import pytest

from app.domain.metal import SchedulerMode
from app.scheduler.calendar import HolidayCalendar
from app.scheduler.engine import AdaptiveScheduler, TokenBucketRateLimiter
from app.scheduler.staleness import compute_staleness
from app.storage.repository import RateRecord

IST = ZoneInfo("Asia/Kolkata")


class MockCalendar(HolidayCalendar):
    def __init__(self, holidays: set[date]):
        self._holidays = holidays


@pytest.fixture
def test_calendar():
    return MockCalendar(holidays={date(2026, 1, 26), date(2026, 8, 15)})


@pytest.fixture
def scheduler(test_calendar):
    return AdaptiveScheduler(holiday_calendar=test_calendar)


def test_scheduler_ist_mode_transitions(scheduler):
    # Monday 02 Nov 2026 (business day)
    # 1. 11:54 IST (Before morning hot window)
    t_1154 = datetime(2026, 11, 2, 11, 54, tzinfo=IST)
    assert scheduler.determine_mode(t_1154) == SchedulerMode.IDLE

    # 2. 11:55 IST (AM Hot window opens)
    t_1155 = datetime(2026, 11, 2, 11, 55, tzinfo=IST)
    assert scheduler.determine_mode(t_1155) == SchedulerMode.HOT

    # 3. 12:15 IST without AM rate captured -> HOT
    t_1215 = datetime(2026, 11, 2, 12, 15, tzinfo=IST)
    assert scheduler.determine_mode(t_1215, session_am_captured=False) == SchedulerMode.HOT

    # 4. 12:15 IST with AM rate captured -> Drops to IDLE
    assert scheduler.determine_mode(t_1215, session_am_captured=True) == SchedulerMode.IDLE

    # 5. 12:41 IST without AM rate (46 mins in) -> CATCH_UP
    t_1241 = datetime(2026, 11, 2, 12, 41, tzinfo=IST)
    assert scheduler.determine_mode(t_1241, session_am_captured=False) == SchedulerMode.CATCH_UP

    # 6. 14:46 IST (window end + 2h expired) -> IDLE
    t_1446 = datetime(2026, 11, 2, 14, 46, tzinfo=IST)
    assert scheduler.determine_mode(t_1446, session_am_captured=False) == SchedulerMode.IDLE

    # 7. 16:55 IST (PM Hot window opens)
    t_1655 = datetime(2026, 11, 2, 16, 55, tzinfo=IST)
    assert scheduler.determine_mode(t_1655) == SchedulerMode.HOT

    # 8. 17:41 IST without PM rate -> CATCH_UP
    t_1741 = datetime(2026, 11, 2, 17, 41, tzinfo=IST)
    assert scheduler.determine_mode(t_1741, session_pm_captured=False) == SchedulerMode.CATCH_UP

    # 9. 17:15 IST with PM captured -> IDLE
    t_1715 = datetime(2026, 11, 2, 17, 15, tzinfo=IST)
    assert scheduler.determine_mode(t_1715, session_pm_captured=True) == SchedulerMode.IDLE

    # 10. 20:00 IST -> IDLE
    t_2000 = datetime(2026, 11, 2, 20, 0, tzinfo=IST)
    assert scheduler.determine_mode(t_2000) == SchedulerMode.IDLE


def test_scheduler_weekend_and_holiday_mode(scheduler):
    # Saturday 31 Oct 2026 -> OFF_DAY
    sat_noon = datetime(2026, 10, 31, 12, 5, tzinfo=IST)
    assert scheduler.determine_mode(sat_noon) == SchedulerMode.OFF_DAY

    # Sunday 01 Nov 2026 -> OFF_DAY
    sun_eve = datetime(2026, 11, 1, 17, 5, tzinfo=IST)
    assert scheduler.determine_mode(sun_eve) == SchedulerMode.OFF_DAY

    # Republic Day (Monday 26 Jan 2026, in mock holidays) -> OFF_DAY
    holiday_noon = datetime(2026, 1, 26, 12, 5, tzinfo=IST)
    assert scheduler.determine_mode(holiday_noon) == SchedulerMode.OFF_DAY


@pytest.mark.asyncio
async def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(max_requests=2, window_seconds=0.2)
    t0 = time.time()
    await limiter.acquire()
    await limiter.acquire()
    # 3rd acquire must wait
    await limiter.acquire()
    elapsed = time.time() - t0
    assert elapsed >= 0.15


def test_staleness_computation():
    holidays = {date(2026, 1, 26)}

    rate_today_am = RateRecord(
        id=1,
        rate_date="2026-11-02",
        session="AM",
        metal="silver",
        purity="999",
        price_inr=98500.0,
        unit="per_kg",
        status="valid",
        revision=1,
        first_seen_at="2026-11-02T06:36:12Z",
        source_url="https://ibjarates.com",
        snapshot_id=None,
        created_at="2026-11-02T06:36:12Z",
    )

    rate_yesterday_pm = RateRecord(
        id=2,
        rate_date="2026-10-30",
        session="PM",
        metal="silver",
        purity="999",
        price_inr=98100.0,
        unit="per_kg",
        status="valid",
        revision=1,
        first_seen_at="2026-10-30T11:36:12Z",
        source_url="https://ibjarates.com",
        snapshot_id=None,
        created_at="2026-10-30T11:36:12Z",
    )

    # Case 1: Weekend - never stale
    sat_time = datetime(2026, 10, 31, 14, 0, tzinfo=IST)
    is_stale, reason, next_pub = compute_staleness(rate_yesterday_pm, sat_time, holidays, True)
    assert not is_stale
    assert reason is None
    assert next_pub is not None

    # Case 2: Business day, morning before AM deadline (12:45) - not stale
    mon_morning = datetime(2026, 11, 2, 11, 0, tzinfo=IST)
    is_stale, reason, _ = compute_staleness(rate_yesterday_pm, mon_morning, holidays, True)
    assert not is_stale

    # Case 3: Business day 13:00, no AM captured today - stale
    mon_1300 = datetime(2026, 11, 2, 13, 0, tzinfo=IST)
    is_stale, reason, _ = compute_staleness(rate_yesterday_pm, mon_1300, holidays, True)
    assert is_stale
    assert reason == "not_yet_published"

    # Case 4: Business day 13:00, AM captured today - fresh
    is_stale, reason, _ = compute_staleness(rate_today_am, mon_1300, holidays, True)
    assert not is_stale

    # Case 5: Business day 18:00, PM not captured - stale
    mon_1800 = datetime(2026, 11, 2, 18, 0, tzinfo=IST)
    is_stale, reason, _ = compute_staleness(rate_today_am, mon_1800, holidays, True)
    assert is_stale
    assert reason == "not_yet_published"

    # Case 6: Parser unhealthy - always stale
    is_stale, reason, _ = compute_staleness(rate_today_am, mon_1300, holidays, False)
    assert is_stale
    assert reason == "parser_unhealthy"
