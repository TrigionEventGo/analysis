"""Celery configuration for WeezMon.

Provides Celery application instance configured with Redis broker and result
backend, to be imported by both the FastAPI app and the worker process.
"""
from __future__ import annotations

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "weezmon",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.worker"],
)

# Sensible defaults for reliability
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
