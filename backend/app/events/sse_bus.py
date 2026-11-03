import asyncio
import json
import logging
from typing import AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)


class SubscriberLimitReached(Exception):
    """Raised when the maximum number of concurrent SSE subscribers is reached."""


class SSEEventBus:
    """
    In-memory Server-Sent Events bus with per-client asyncio.Queue fanout.
    """

    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    def has_capacity(self) -> bool:
        return len(self._subscribers) < settings.max_sse_subscribers

    async def subscribe(self, initial_comment: bool = True) -> AsyncGenerator[str, None]:
        """
        Subscribe to SSE feed. Yields formatted SSE strings.
        Also handles keepalive pings every 15s.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if len(self._subscribers) >= settings.max_sse_subscribers:
                raise SubscriberLimitReached()
            self._subscribers.add(queue)

        try:
            if initial_comment:
                yield ": connected\n\n"
            while True:
                try:
                    # Wait for message with 15-second timeout for keepalive ping
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    event_name = payload.get("event", "message")
                    data_json = json.dumps(payload.get("data", {}))
                    yield f"event: {event_name}\ndata: {data_json}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment or ping event
                    yield "event: ping\ndata: {}\n\n"
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    async def publish(self, event_type: str, data: dict) -> None:
        """
        Broadcast an event to all active subscriber queues.
        """
        payload = {"event": event_type, "data": data}
        async with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    logger.warning("Subscriber queue full. Dropping event.")


sse_bus = SSEEventBus()
