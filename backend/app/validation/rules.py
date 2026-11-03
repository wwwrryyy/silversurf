from dataclasses import dataclass
from datetime import datetime
import logging

from app.config import settings
from app.core.time_utils import now_ist
from app.domain.metal import RateStatus
from app.sources.base import RawScrapeResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    status: RateStatus
    error_message: str | None = None
    warning_message: str | None = None


class ValidationPipeline:
    def __init__(
        self,
        min_price: float | None = None,
        max_price: float | None = None,
        dod_threshold: float | None = None,
    ):
        self.min_price = min_price if min_price is not None else settings.min_price_inr
        self.max_price = max_price if max_price is not None else settings.max_price_inr
        self.dod_threshold = dod_threshold if dod_threshold is not None else settings.dod_quarantine_threshold

    def validate_record(
        self,
        record: RawScrapeResult,
        prev_price_inr: float | None = None,
        current_time_ist: datetime | None = None,
    ) -> ValidationResult:
        """
        Execute validation rules V1-V5 on a scraped rate record.
        """
        now_dt = current_time_ist or now_ist()
        today_ist = now_dt.date()

        # Rule V3: Date must be today or past; future dates rejected
        if record.rate_date > today_ist:
            msg = f"V3 Violation: Future date {record.rate_date} rejected (today is {today_ist})"
            logger.error(msg)
            return ValidationResult(
                is_valid=False,
                status=RateStatus.VALID,
                error_message=msg,
            )

        # Rule V1: Price Bounds check (1,000 <= price <= 1,000,000 INR per kg)
        if record.price_inr < self.min_price or record.price_inr > self.max_price:
            msg = f"V1 Violation: Price {record.price_inr} out of plausible bounds [{self.min_price}, {self.max_price}]"
            logger.error(msg)
            return ValidationResult(
                is_valid=False,
                status=RateStatus.VALID,
                error_message=msg,
            )

        # Rule V1 (cont.): whole rupees only, no fractional paise
        if record.price_inr != int(record.price_inr):
            msg = f"V1 Violation: Price {record.price_inr} is not a whole-rupee integer"
            logger.error(msg)
            return ValidationResult(
                is_valid=False,
                status=RateStatus.VALID,
                error_message=msg,
            )

        # Rule V5: Cross-check card vs table (Warning only, does not reject)
        warning_msg: str | None = None
        if record.card_price_inr is not None:
            if abs(record.card_price_inr - record.price_inr) > 1.0:
                warning_msg = (
                    f"V5 Warning: Mismatch between table ({record.price_inr}) and card ({record.card_price_inr})"
                )
                logger.warning(warning_msg)

        # Rule V2: Day-over-Day move > 12% moves record to quarantine
        if prev_price_inr and prev_price_inr > 0:
            dod_move = abs(record.price_inr - prev_price_inr) / prev_price_inr
            if dod_move > self.dod_threshold:
                dod_msg = (
                    f"V2 Quarantine: Day-over-day price move {dod_move:.2%} exceeds threshold "
                    f"{self.dod_threshold:.2%} (prev={prev_price_inr}, curr={record.price_inr})"
                )
                logger.warning(dod_msg)
                return ValidationResult(
                    is_valid=True,
                    status=RateStatus.QUARANTINED,
                    warning_message=dod_msg,
                )

        return ValidationResult(
            is_valid=True,
            status=RateStatus.VALID,
            warning_message=warning_msg,
        )
