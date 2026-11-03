from datetime import date
from pathlib import Path
import yaml
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class HolidayCalendar:
    def __init__(self, holidays_file_path: str | Path | None = None):
        self.file_path = Path(holidays_file_path or settings.holidays_file)
        self._holidays: set[date] = set()
        self.load()

    def load(self) -> set[date]:
        """Load or reload holiday dates from YAML file."""
        if not self.file_path.exists():
            logger.warning(f"Holiday calendar file {self.file_path} not found. Using empty set.")
            self._holidays = set()
            return self._holidays

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                raw_list = data.get("holidays", [])
                self._holidays = {date.fromisoformat(str(d)) for d in raw_list}
        except Exception as exc:
            logger.error(f"Error loading holiday calendar from {self.file_path}: {exc}")
            self._holidays = set()

        return self._holidays

    def is_holiday(self, check_date: date) -> bool:
        return check_date in self._holidays

    def is_business_day(self, check_date: date) -> bool:
        # 5 = Saturday, 6 = Sunday
        if check_date.weekday() >= 5:
            return False
        return check_date not in self._holidays

    @property
    def holidays(self) -> set[date]:
        return self._holidays
