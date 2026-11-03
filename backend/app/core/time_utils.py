from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UTC = timezone.utc


def now_ist() -> datetime:
    """Return the current datetime in Asia/Kolkata timezone."""
    return datetime.now(IST)


def now_utc() -> datetime:
    """Return current datetime in UTC."""
    return datetime.now(UTC)


def parse_dd_mm_yyyy_ist(date_str: str) -> date:
    """
    Parse a 'DD/MM/YYYY' date string published on ibjarates.com.
    Example: '02/11/2026' -> date(2026, 11, 2)
    """
    cleaned = date_str.strip()
    return datetime.strptime(cleaned, "%d/%m/%Y").date()


def to_utc_iso(dt: datetime | None) -> str | None:
    """Convert datetime to ISO-8601 UTC string (ending with Z)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(iso_str: str | None) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp."""
    if not iso_str:
        return None
    cleaned = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


def parse_hhmm(value: str) -> time:
    """Parse an 'HH:MM' string into a time."""
    hh, mm = value.split(":")
    return time(int(hh), int(mm))
