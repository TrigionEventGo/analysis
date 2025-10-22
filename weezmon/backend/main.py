"""FastAPI entrypoint for WeezMon backend.

Exposes health check and domain routers. All endpoints are async and use
Pydantic models. Business logic is delegated to services modules.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.utils.logger import logger
from backend.routers.companies import router as companies_router
from backend.routers.events import router as events_router
from backend.routers.finance import router as finance_router
from backend.routers.reports import router as reports_router

APP_NAME = os.getenv("APP_NAME", "weezmon-backend")

app = FastAPI(title="WeezMon Backend", version="0.1.0")

# Allow local dev and common hosts by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Simple health endpoint to verify service readiness."""
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "app": APP_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Routers
app.include_router(companies_router, prefix="/companies", tags=["companies"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(finance_router, prefix="/finance", tags=["finance"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
