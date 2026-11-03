from datetime import date, datetime
from zoneinfo import ZoneInfo
import pytest

from app.domain.metal import Metal, RateStatus, Session
from app.sources.base import RawScrapeResult
from app.validation.rules import ValidationPipeline

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def validator():
    return ValidationPipeline(min_price=1000.0, max_price=1000000.0, dod_threshold=0.12)


def test_v1_price_bounds_rejection(validator):
    now_ist = datetime(2026, 11, 2, 12, 10, tzinfo=IST)

    # Below min price
    low_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=500.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
    )
    res = validator.validate_record(low_record, current_time_ist=now_ist)
    assert not res.is_valid
    assert "V1 Violation" in (res.error_message or "")

    # Above max price
    high_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=1500000.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
    )
    res = validator.validate_record(high_record, current_time_ist=now_ist)
    assert not res.is_valid
    assert "V1 Violation" in (res.error_message or "")


def test_v2_dod_spike_quarantine(validator):
    now_ist = datetime(2026, 11, 2, 12, 10, tzinfo=IST)

    # 100,000 -> 115,000 is a 15% increase (> 12%)
    spike_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=115000.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
    )
    res = validator.validate_record(spike_record, prev_price_inr=100000.0, current_time_ist=now_ist)
    assert res.is_valid
    assert res.status == RateStatus.QUARANTINED
    assert "V2 Quarantine" in (res.warning_message or "")

    # 100,000 -> 105,000 is 5% increase (< 12%)
    normal_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=105000.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
    )
    res_normal = validator.validate_record(normal_record, prev_price_inr=100000.0, current_time_ist=now_ist)
    assert res_normal.is_valid
    assert res_normal.status == RateStatus.VALID


def test_v3_future_date_rejected(validator):
    now_ist = datetime(2026, 11, 2, 12, 10, tzinfo=IST)

    future_record = RawScrapeResult(
        rate_date=date(2026, 11, 3),  # Tomorrow
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=98500.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
    )
    res = validator.validate_record(future_record, current_time_ist=now_ist)
    assert not res.is_valid
    assert "V3 Violation" in (res.error_message or "")


def test_v5_cross_check_warning(validator):
    now_ist = datetime(2026, 11, 2, 12, 10, tzinfo=IST)

    mismatch_record = RawScrapeResult(
        rate_date=date(2026, 11, 2),
        session=Session.AM,
        metal=Metal.SILVER,
        purity="999",
        price_inr=98500.0,
        unit="per_kg",
        raw_html_bytes=b"",
        http_status=200,
        source_url="",
        card_price_inr=99200.0,  # Diverges
    )
    res = validator.validate_record(mismatch_record, current_time_ist=now_ist)
    assert res.is_valid
    assert res.status == RateStatus.VALID
    assert "V5 Warning" in (res.warning_message or "")
