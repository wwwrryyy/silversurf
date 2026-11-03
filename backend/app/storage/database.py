from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import aiosqlite

from app.config import settings

MIGRATION_FILE = Path(__file__).parent / "migrations" / "001_initial_schema.sql"


async def init_db(db_path: str | None = None) -> None:
    """Initialize database tables and WAL configuration."""
    path = db_path or settings.database_path
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        await db.execute("PRAGMA foreign_keys = ON;")

        if MIGRATION_FILE.exists():
            schema_sql = MIGRATION_FILE.read_text(encoding="utf-8")
            await db.executescript(schema_sql)

        await db.commit()


@asynccontextmanager
async def get_connection(db_path: str | None = None) -> AsyncIterator[aiosqlite.Connection]:
    """Provide an async connection with row_factory and WAL pragmas."""
    path = db_path or settings.database_path
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA busy_timeout = 5000;")
        await conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
