from datetime import datetime, date, time, timedelta

from app.config import settings
from app.core.time_utils import IST, parse_hhmm, to_utc_iso
from app.storage.repository import RateRecord


def calculate_next_business_window(now_ist_dt: datetime, holiday_calendar: set[date]) -> datetime:
    """
    Calculate the next publication window (either today 12:05 or 17:05, or next business day 12:05).
    """
    today = now_ist_dt.date()
    current_time = now_ist_dt.time()
    is_biz_today = (now_ist_dt.weekday() < 5) and (today not in holiday_calendar)

    if is_biz_today:
        if current_time < time(12, 5):
            return datetime.combine(today, time(12, 5), tzinfo=IST)
        if current_time < time(17, 5):
            return datetime.combine(today, time(17, 5), tzinfo=IST)

    # Search for next business day starting tomorrow
    candidate = today + timedelta(days=1)
    while candidate.weekday() >= 5 or candidate in holiday_calendar:
        candidate += timedelta(days=1)

    return datetime.combine(candidate, time(12, 5), tzinfo=IST)


def compute_staleness(
    latest_rate: RateRecord | None,
    now_ist_dt: datetime,
    holiday_calendar: set[date],
    scheduler_healthy: bool,
    last_scrape_failed: bool = False,
) -> tuple[bool, str | None, str | None]:
    """
    Determine staleness, stale_reason, and next_expected_publication.
    Returns: (is_stale, stale_reason, next_expected_publication_utc_iso)
    """
    next_pub = calculate_next_business_window(now_ist_dt, holiday_calendar)
    next_pub_iso = to_utc_iso(next_pub)

    if latest_rate is None:
        return True, "not_yet_published", next_pub_iso

    if not scheduler_healthy:
        return True, "parser_unhealthy", next_pub_iso

    today = now_ist_dt.date()
    today_str = today.isoformat()
    is_weekend = now_ist_dt.weekday() >= 5
    is_holiday = today in holiday_calendar

    # On non-business days, rates are not stale
    if is_weekend or is_holiday:
        return False, None, next_pub_iso

    # Business day logic
    am_deadline = parse_hhmm(settings.hot_window_am_end)
    pm_deadline = parse_hhmm(settings.hot_window_pm_end)
    current_time = now_ist_dt.time()

    if current_time > pm_deadline:
        # Expected today's PM rate
        if latest_rate.rate_date < today_str or latest_rate.session != "PM":
            return True, ("source_unavailable" if last_scrape_failed else "not_yet_published"), next_pub_iso
        return False, None, next_pub_iso

    if current_time > am_deadline:
        # Expected today's AM rate
        if latest_rate.rate_date < today_str or latest_rate.session not in ("AM", "PM"):
            return True, ("source_unavailable" if last_scrape_failed else "not_yet_published"), next_pub_iso
        return False, None, next_pub_iso

    # Before AM deadline: today's morning rate is not yet overdue
    return False, None, next_pub_iso
