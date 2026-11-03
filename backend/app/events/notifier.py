import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or settings.notification_webhook_url

    async def send_alert(self, title: str, message: str, severity: str = "info") -> None:
        if not self.webhook_url:
            return

        payload = {
            "title": f"[{severity.upper()}] {title}",
            "message": message,
            "topic": "silversurf",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.webhook_url, json=payload)
        except Exception as exc:
            logger.error("Failed to send webhook notification: %s", exc)


notifier = Notifier()
