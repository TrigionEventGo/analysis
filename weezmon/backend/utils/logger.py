"""Centralized logging configuration for the backend services.

This module exposes a configured logger instance that standardizes log
formatting across the application, including the Celery worker.
"""
from __future__ import annotations

import logging
import os

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _create_logger() -> logging.Logger:
    logger = logging.getLogger("weezmon")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.setLevel(_LOG_LEVEL)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = _create_logger()
