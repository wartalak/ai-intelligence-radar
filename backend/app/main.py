"""
FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.init_db import init_db, seed_sources
from app.api.reports import router as reports_router
from app.api.trends import router as trends_router
from app.api.content import router as content_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    await seed_sources()
    yield


app = FastAPI(
    title="AI Intelligence Radar",
    description="Automated AI ecosystem intelligence reports",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──
app.include_router(reports_router, prefix="/api", tags=["Reports"])
app.include_router(trends_router, prefix="/api", tags=["Trends"])
app.include_router(content_router, prefix="/api", tags=["Content"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-intelligence-radar"}
