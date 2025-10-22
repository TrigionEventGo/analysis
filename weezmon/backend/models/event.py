"""Pydantic model for events."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Event(BaseModel):
    id: str
    company_id: str
    event_guid: str
    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
