"""Pydantic model for orders."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Order(BaseModel):
    id: str
    event_id: str
    total: float
    status: str
    created_at: datetime | None = None
