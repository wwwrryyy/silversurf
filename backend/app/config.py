from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SilverSurf"
    environment: str = "production"
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"

    # Storage
    database_path: str = "silversurf.db"
    snapshots_dir: str = "snapshots"
    snapshot_retention_days: int = 90
    scrape_run_retention_days: int = 180

    # Source & Scraping
    source_url: str = "https://ibjarates.com/"
    user_agent: str = "SilverSurf/1.0 (+https://github.com/shawnsc/silversurf; contact@example.com)"
    request_timeout_seconds: float = 15.0
    rate_limit_per_minute: int = 2

    # Validation Rules
    min_price_inr: float = 1000.0
    max_price_inr: float = 1000000.0
    dod_quarantine_threshold: float = 0.12  # >12% DoD move

    # Scheduling & Windows
    holidays_file: str = str(Path(__file__).parent / "scheduler" / "holidays.yaml")
    hot_window_am_start: str = "11:55"
    hot_window_am_end: str = "12:45"
    hot_window_pm_start: str = "16:55"
    hot_window_pm_end: str = "17:45"
    catch_up_poll_interval_seconds: int = 120   # 2 minutes
    hot_poll_interval_seconds: int = 30        # 30 seconds
    idle_poll_interval_seconds: int = 900      # 15 minutes
    off_day_poll_interval_seconds: int = 21600 # 6 hours

    # Security & limits
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    admin_token: str | None = None
    max_sse_subscribers: int = 50
    max_http_response_bytes: int = 10 * 1024 * 1024
    allowed_scrape_hosts: list[str] = ["ibjarates.com", "www.ibjarates.com"]

    # Webhook / Notifier (Scale-up / alerts)
    notification_webhook_url: str | None = None


settings = Settings()
