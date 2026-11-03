from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.config import settings
from app.scheduler.engine import AdaptiveScheduler
from app.storage.database import init_db

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("silversurf")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Initializing SilverSurf database at %s...", settings.database_path)
    await init_db()

    # Initialize scheduler
    scheduler = AdaptiveScheduler()
    app.state.scheduler = scheduler

    # Start background scheduler unless disabled by environment (e.g. testing)
    if settings.environment != "testing":
        await scheduler.start()

    yield

    if settings.environment != "testing":
        await scheduler.stop()
    logger.info("SilverSurf backend shutdown complete.")


app = FastAPI(
    title="SilverSurf API",
    description="Resilient, low-latency monitoring service and real-time feed for IBJA Silver 999 benchmark rates",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Admin-Token"],
)

app.include_router(v1_router)


@app.get("/")
async def root():
    return {
        "service": "SilverSurf API",
        "version": "1.0.0",
        "documentation": "/docs",
        "latest": "/v1/silver/latest",
    }
