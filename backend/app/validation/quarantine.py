import logging
import aiosqlite
from app.storage.repository import RateRecord

logger = logging.getLogger(__name__)


class QuarantineManager:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def list_quarantined(self) -> list[RateRecord]:
        """Fetch all records currently in quarantine."""
        async with self.conn.execute(
            """
            SELECT * FROM rates
            WHERE status = 'quarantined'
            ORDER BY rate_date DESC, session DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [RateRecord.from_row(r) for r in rows]

    async def approve_record(self, rate_id: int) -> bool:
        """
        Manually approve a quarantined record, moving its status to 'valid'.
        """
        cursor = await self.conn.execute(
            """
            UPDATE rates
            SET status = 'valid'
            WHERE id = ? AND status = 'quarantined'
            """,
            (rate_id,),
        )
        await self.conn.commit()
        approved = cursor.rowcount > 0
        if approved:
            logger.info("Quarantined rate id %d approved and set to valid", rate_id)
        return approved
