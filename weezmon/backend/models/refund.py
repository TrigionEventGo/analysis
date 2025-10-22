"""Pydantic model for refunds."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Refund(BaseModel):
    id: str
    order_id: str
    amount: float
    status: str
    created_at: datetime | None = None
